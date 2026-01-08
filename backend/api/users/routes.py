"""
User Management API Routes
"""
import logging
import json
from fastapi import APIRouter, HTTPException
from typing import List
from bson import ObjectId
from datetime import datetime

from database.mongodb import get_mongodb
from core.llm.router import LLMRouter
from .schemas import (
    UserProfileCreate,
    UserProfileUpdate,
    UserProfileResponse,
    UserProfileList,
    SetActiveUserRequest,
    AIExtractRequest,
    AIExtractResponse,
    Experience,
    Education,
    Language
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/users", tags=["Users"])

# Initialize LLM router
llm_router = LLMRouter()


def _user_to_response(user_doc: dict) -> UserProfileResponse:
    """Convert MongoDB document to UserProfileResponse"""
    user_doc["id"] = str(user_doc.pop("_id"))
    return UserProfileResponse(**user_doc)


@router.get("", response_model=UserProfileList)
async def list_users():
    """List all user profiles"""
    db = get_mongodb()
    
    users = list(db.db.user_profiles.find())
    total = len(users)
    active_user_id = db.get_active_user_id()
    
    return UserProfileList(
        users=[_user_to_response(u) for u in users],
        total=total,
        active_user_id=active_user_id
    )


@router.post("", response_model=UserProfileResponse, status_code=201)
async def create_user(user_data: UserProfileCreate):
    """Create a new user profile"""
    db = get_mongodb()
    
    # Check if profile_name already exists
    existing = db.db.user_profiles.find_one({"profile_name": user_data.profile_name})
    if existing:
        raise HTTPException(400, f"Profile name '{user_data.profile_name}' already exists")
    
    # Prepare document
    user_dict = user_data.dict()
    user_dict["created_at"] = datetime.utcnow()
    user_dict["updated_at"] = datetime.utcnow()
    
    # Insert
    result = db.db.user_profiles.insert_one(user_dict)
    user_id = str(result.inserted_id)
    
    logger.info(f"✅ Created user profile: {user_data.profile_name} (ID: {user_id})")
    
    # If this is the first/only user, set as active
    user_count = db.db.user_profiles.count_documents({})
    if user_count == 1:
        db.set_active_user_id(user_id)
        logger.info(f"🌟 Set first user as active: {user_id}")
    
    # Fetch and return
    user_doc = db.db.user_profiles.find_one({"_id": result.inserted_id})
    return _user_to_response(user_doc)


@router.get("/{user_id}", response_model=UserProfileResponse)
async def get_user(user_id: str):
    """Get a specific user  profile"""
    db = get_mongodb()
    
    try:
        user_doc = db.db.user_profiles.find_one({"_id": ObjectId(user_id)})
    except Exception:
        raise HTTPException(400, "Invalid user ID format")
    
    if not user_doc:
        raise HTTPException(404, f"User {user_id} not found")
    
    return _user_to_response(user_doc)


@router.put("/{user_id}", response_model=UserProfileResponse)
async def update_user(user_id: str, user_data: UserProfileUpdate):
    """Update user profile"""
    db = get_mongodb()
    
    try:
        obj_id = ObjectId(user_id)
    except Exception:
        raise HTTPException(400, "Invalid user ID format")
    
    # Check user exists
    existing = db.db.user_profiles.find_one({"_id": obj_id})
    if not existing:
        raise HTTPException(404, f"User {user_id} not found")
    
    # If changing profile_name, check uniqueness
    if user_data.profile_name and user_data.profile_name != existing.get("profile_name"):
        duplicate = db.db.user_profiles.find_one({"profile_name": user_data.profile_name})
        if duplicate:
            raise HTTPException(400, f"Profile name '{user_data.profile_name}' already exists")
    
    # Prepare update (exclude None values)
    update_dict = {k: v for k, v in user_data.dict().items() if v is not None}
    update_dict["updated_at"] = datetime.utcnow()
    
    # Update
    db.db.user_profiles.update_one(
        {"_id": obj_id},
        {"$set": update_dict}
    )
    
    logger.info(f"✅ Updated user profile: {user_id}")
    
    # Fetch and return
    user_doc = db.db.user_profiles.find_one({"_id": obj_id})
    return _user_to_response(user_doc)


@router.delete("/{user_id}", status_code=204)
async def delete_user(user_id: str):
    """Delete user profile"""
    db = get_mongodb()
    
    try:
        obj_id = ObjectId(user_id)
    except Exception:
        raise HTTPException(400, "Invalid user ID format")
    
    # Check user exists
    existing = db.db.user_profiles.find_one({"_id": obj_id})
    if not existing:
        raise HTTPException(404, f"User {user_id} not found")
    
    # If deleting active user, clear active user
    active_user_id = db.get_active_user_id()
    if active_user_id == user_id:
        db.db.app_config.delete_one({"_id": "active_user_config"})
        logger.info("⚠️  Deleted active user - active user cleared")
    
    # Delete
    db.db.user_profiles.delete_one({"_id": obj_id})
    logger.info(f"✅ Deleted user profile: {user_id}")


@router.get("/active/current", response_model=UserProfileResponse)
async def get_active_user():
    """Get currently active user"""
    db = get_mongodb()
    
    active_user_id = db.get_active_user_id()
    if not active_user_id:
        # Try to auto-select if only one user exists
        users = list(db.db.user_profiles.find().limit(2))
        if len(users) == 1:
            user_id = str(users[0]["_id"])
            db.set_active_user_id(user_id)
            logger.info(f"🌟 Auto-selected only user as active: {user_id}")
            return _user_to_response(users[0])
        
        raise HTTPException(404, "No active user set. Please select a user first.")
    
    try:
        user_doc = db.db.user_profiles.find_one({"_id": ObjectId(active_user_id)})
    except Exception:
        raise HTTPException(500, "Invalid active user ID in database")
    
    if not user_doc:
        raise HTTPException(404, f"Active user {active_user_id} not found in database")
    
    return _user_to_response(user_doc)


@router.put("/active/set", status_code=200)
async def set_active_user(request: SetActiveUserRequest):
    """Set active user"""
    db = get_mongodb()
    
    # Validate user exists
    try:
        obj_id = ObjectId(request.user_id)
    except Exception:
        raise HTTPException(400, "Invalid user ID format")
    
    user_doc = db.db.user_profiles.find_one({"_id": obj_id})
    if not user_doc:
        raise HTTPException(404, f"User {request.user_id} not found")
    
    # Set active
    db.set_active_user_id(request.user_id)
    
    return {
        "success": True,
        "active_user_id": request.user_id,
        "message": f"Active user set to: {user_doc['nome']}"
    }


@router.post("/ai-extract", response_model=AIExtractResponse)
async def extract_profile_with_ai(request: AIExtractRequest):
    """
    Extract structured profile data from natural language text using AI.
    
    Users can paste their CV, LinkedIn summary, or describe their background naturally.
    The AI will extract:
    - Work experiences
    - Education
    - Skills
    - Languages
    """
    logger.info(f"🤖 AI extraction requested ({len(request.text)} chars)")
    
    # Build extraction prompt
    prompt = f"""You are a professional CV parser. Extract structured profile information from the text below.

CRITICAL RULES:
1. Return ONLY valid JSON, NO explanations or additional text
2. If information is missing, use empty arrays
3. Dates format: "Month YYYY - Month YYYY" or "YYYY - YYYY"
4. Extract ALL skills mentioned (technologies, tools, methodologies)
5. For experiences: company, role, period, description, technologies, achievements

OUTPUT FORMAT (EXACT JSON):
{{
    "experiencias": [
        {{
            "empresa": "Company name",
            "cargo": "Job title",
            "periodo": "Period",
            "descricao": "Brief description",
            "tecnologias": ["Tech1", "Tech2"],
            "realizacoes": ["Achievement 1", "Achievement 2"]
        }}
    ],
    "educacao": [
        {{
            "instituicao": "Institution name",
            "curso": "Degree/Course",
            "periodo": "Period"
        }}
    ],
    "habilidades": ["Skill1", "Skill2"],
    "idiomas": [
        {{
            "idioma": "Language",
            "nivel": "Proficiency level"
        }}
    ]
}}

TEXT TO PARSE:
{request.text}

JSON OUTPUT:"""

    try:
        # Call LLM (using local Llama to avoid API costs)
        llm_response = await llm_router.generate(
            prompt=prompt,
            model="llama3.1:8b",  # Use local Llama (no cost!)
            temperature=0.3  # Low temperature for structured output
        )
        
        logger.info(f"🤖 LLM response: {llm_response[:200]}...")
        
        # Clean response (sometimes LLM adds markdown)
        cleaned_response = llm_response.strip()
        if cleaned_response.startswith("```json"):
            cleaned_response = cleaned_response[7:]
        if cleaned_response.startswith("```"):
            cleaned_response = cleaned_response[3:]
        if cleaned_response.endswith("```"):
            cleaned_response = cleaned_response[:-3]
        cleaned_response = cleaned_response.strip()
        
        # Parse JSON
        extracted_data = json.loads(cleaned_response)
        
        # Validate and convert to schema objects
        experiencias = [Experience(**exp) for exp in extracted_data.get("experiencias", [])]
        educacao = [Education(**edu) for edu in extracted_data.get("educacao", [])]
        habilidades = extracted_data.get("habilidades", [])
        idiomas = [Language(**lang) for lang in extracted_data.get("idiomas", [])]
        
        logger.info(f"✅ Extracted: {len(experiencias)} exp, {len(educacao)} edu, {len(habilidades)} skills")
        
        return AIExtractResponse(
            experiencias=experiencias,
            educacao=educacao,
            habilidades=habilidades,
            idiomas=idiomas,
            success=True,
            message=f"Extraído: {len(experiencias)} experiências, {len(educacao)} formações, {len(habilidades)} habilidades"
        )
        
    except json.JSONDecodeError as e:
        logger.error(f"❌ JSON parse error: {e}")
        logger.error(f"LLM response was: {llm_response}")
        raise HTTPException(
            500,
            f"Erro ao processar resposta da IA. Por favor, tente novamente ou forneça mais detalhes."
        )
    except Exception as e:
        logger.error(f"❌ AI extraction error: {e}")
        raise HTTPException(500, f"Erro na extração: {str(e)}")

import React, { useEffect, useMemo, useState } from 'react';

const API_BASE = import.meta.env.VITE_API_BASE || 'http://127.0.0.1:8000';

const emptyUserForm = {
  profile_name: '',
  nome: '',
  cargo_atual: '',
  email: '',
  telefone: '',
  linkedin: '',
  github: '',
  cidade: '',
  estado: '',
  experiencias: [createExperience()],
  educacao: [createEducation()],
  habilidades: [],
  idiomas: []
};

function createExperience() {
  return {
    empresa: '',
    cargo: '',
    periodo: '',
    descricao: '',
    tecnologias: [],
    realizacoes: []
  };
}

function createEducation() {
  return {
    instituicao: '',
    curso: '',
    periodo: ''
  };
}

function createLanguage() {
  return {
    idioma: '',
    nivel: ''
  };
}

function App() {
  const [activeTab, setActiveTab] = useState('resume');
  const [health, setHealth] = useState({ status: 'Verificando...', online: false });
  const [users, setUsers] = useState([]);
  const [activeUserId, setActiveUserId] = useState(null);
  const [jobs, setJobs] = useState([]);
  const [selectedJobId, setSelectedJobId] = useState(null);
  const [variants, setVariants] = useState([]);
  const [variantCount, setVariantCount] = useState(3);
  const [jobContent, setJobContent] = useState('');
  const [resumeStatus, setResumeStatus] = useState('');
  const [resumeStatusError, setResumeStatusError] = useState(false);
  const [userStatus, setUserStatus] = useState('');
  const [userStatusError, setUserStatusError] = useState(false);
  const [editingUserId, setEditingUserId] = useState(null);
  const [userForm, setUserForm] = useState(emptyUserForm);
  const [skillInput, setSkillInput] = useState('');
  const [previewVariant, setPreviewVariant] = useState(null);

  useEffect(() => {
    void initialize();
  }, []);

  const activeUser = useMemo(
    () => users.find((user) => user.id === activeUserId) || null,
    [users, activeUserId]
  );

  const selectedJob = useMemo(
    () => jobs.find((job) => job.job_id === selectedJobId) || null,
    [jobs, selectedJobId]
  );

  async function initialize() {
    await Promise.all([loadHealth(), loadUsers(), loadHistory()]);
  }

  async function apiFetch(path, options = {}) {
    const response = await fetch(`${API_BASE}${path}`, {
      headers: {
        'Content-Type': 'application/json',
        ...(options.headers || {})
      },
      ...options
    });

    if (!response.ok) {
      let message = 'Erro inesperado';
      try {
        const payload = await response.json();
        message = payload.detail || payload.message || message;
      } catch {
        message = response.statusText || message;
      }
      throw new Error(message);
    }

    if (response.status === 204) {
      return null;
    }

    const contentType = response.headers.get('content-type') || '';
    if (contentType.includes('application/json')) {
      return response.json();
    }

    return response;
  }

  async function loadHealth() {
    try {
      const payload = await apiFetch('/health');
      setHealth({ status: 'Online', online: true, payload });
    } catch (error) {
      setHealth({ status: 'Offline', online: false, error: error.message });
    }
  }

  async function loadUsers() {
    try {
      const payload = await apiFetch('/api/users');
      setUsers(payload.users);
      setActiveUserId(payload.active_user_id);
    } catch (error) {
      setUsers([]);
      setActiveUserId(null);
      setUserStatus(error.message);
      setUserStatusError(true);
    }
  }

  async function loadHistory(targetJobId = null) {
    try {
      const payload = await apiFetch('/api/resume/history');
      setJobs(payload);

      const nextSelectedJobId = targetJobId || selectedJobId;
      const nextSelected = payload.find((job) => job.job_id === nextSelectedJobId) || payload[0] || null;

      if (nextSelected) {
        setSelectedJobId(nextSelected.job_id);
        await loadVariants(nextSelected.job_id);
      } else {
        setSelectedJobId(null);
        setVariants([]);
      }
    } catch (error) {
      setJobs([]);
      setSelectedJobId(null);
      setVariants([]);
      setResumeStatus(error.message);
      setResumeStatusError(true);
    }
  }

  async function loadVariants(jobId) {
    try {
      const payload = await apiFetch(`/api/resume/jobs/${jobId}/variants`);
      setVariants(payload);
    } catch (error) {
      setVariants([]);
      setResumeStatus(error.message);
      setResumeStatusError(true);
    }
  }

  async function handleCreateJob(event) {
    event.preventDefault();

    if (!activeUserId) {
      setResumeStatus('Cadastre e ative um usuário antes de gerar CVs.');
      setResumeStatusError(true);
      setActiveTab('users');
      return;
    }

    if (!jobContent.trim()) {
      setResumeStatus('Cole a descrição da vaga.');
      setResumeStatusError(true);
      return;
    }

    try {
      setResumeStatusError(false);
      setResumeStatus('Criando vaga...');

      const job = await apiFetch('/api/resume/jobs', {
        method: 'POST',
        body: JSON.stringify({
          input_type: 'text',
          content: jobContent.trim()
        })
      });

      setResumeStatus('Gerando variantes...');

      await apiFetch(`/api/resume/jobs/${job.id}/generate`, {
        method: 'POST',
        body: JSON.stringify({ count: variantCount })
      });

      setJobContent('');
      setResumeStatus('CVs gerados com sucesso.');
      await loadHealth();
      await loadHistory(job.id);
    } catch (error) {
      setResumeStatus(error.message);
      setResumeStatusError(true);
    }
  }

  async function handleGenerateMore() {
    if (!selectedJobId) {
      return;
    }

    try {
      setResumeStatusError(false);
      setResumeStatus('Gerando novas variantes...');
      await apiFetch(`/api/resume/jobs/${selectedJobId}/generate-more?count=${variantCount}`, {
        method: 'POST'
      });
      setResumeStatus('Novas variantes geradas.');
      await loadHealth();
      await loadHistory(selectedJobId);
    } catch (error) {
      setResumeStatus(error.message);
      setResumeStatusError(true);
    }
  }

  async function handleDeleteJob() {
    if (!selectedJob) {
      return;
    }

    if (!window.confirm(`Excluir a vaga "${selectedJob.job_title}"?`)) {
      return;
    }

    try {
      await apiFetch(`/api/resume/jobs/${selectedJob.job_id}`, { method: 'DELETE' });
      setResumeStatus('Vaga removida.');
      setResumeStatusError(false);
      await loadHealth();
      await loadHistory();
    } catch (error) {
      setResumeStatus(error.message);
      setResumeStatusError(true);
    }
  }

  async function handleDeleteVariant(variantId) {
    if (!window.confirm('Excluir esta variante?')) {
      return;
    }

    try {
      await apiFetch(`/api/resume/variants/${variantId}`, { method: 'DELETE' });
      setResumeStatus('Variante removida.');
      setResumeStatusError(false);
      await loadHealth();
      if (selectedJobId) {
        await loadHistory(selectedJobId);
      }
    } catch (error) {
      setResumeStatus(error.message);
      setResumeStatusError(true);
    }
  }

  async function handleDownloadVariant(variantId) {
    try {
      const response = await fetch(`${API_BASE}/api/resume/variants/${variantId}/download`);
      if (!response.ok) {
        throw new Error('Falha no download do arquivo.');
      }

      const blob = await response.blob();
      const url = URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `cv_${variantId}.docx`;
      link.click();
      URL.revokeObjectURL(url);
    } catch (error) {
      setResumeStatus(error.message);
      setResumeStatusError(true);
    }
  }

  async function handleSetActiveUser(userId) {
    try {
      await apiFetch('/api/users/active/set', {
        method: 'PUT',
        body: JSON.stringify({ user_id: userId })
      });
      setUserStatus('Usuário ativo atualizado.');
      setUserStatusError(false);
      await Promise.all([loadHealth(), loadUsers()]);
    } catch (error) {
      setUserStatus(error.message);
      setUserStatusError(true);
    }
  }

  function startEditingUser(user) {
    setEditingUserId(user.id);
    setUserStatus('');
    setUserStatusError(false);
    setActiveTab('users');
    setUserForm({
      profile_name: user.profile_name || '',
      nome: user.nome || '',
      cargo_atual: user.cargo_atual || '',
      email: user.email || '',
      telefone: user.telefone || '',
      linkedin: user.linkedin || '',
      github: user.github || '',
      cidade: user.cidade || '',
      estado: user.estado || '',
      experiencias: user.experiencias?.length ? user.experiencias.map((item) => ({ ...item })) : [createExperience()],
      educacao: user.educacao?.length ? user.educacao.map((item) => ({ ...item })) : [createEducation()],
      habilidades: user.habilidades ? [...user.habilidades] : [],
      idiomas: user.idiomas?.length ? user.idiomas.map((item) => ({ ...item })) : []
    });
  }

  async function handleDeleteUser(user) {
    if (!window.confirm(`Excluir o usuário "${user.nome}"?`)) {
      return;
    }

    try {
      await apiFetch(`/api/users/${user.id}`, { method: 'DELETE' });
      if (editingUserId === user.id) {
        resetUserForm();
      }
      setUserStatus('Usuário removido.');
      setUserStatusError(false);
      await Promise.all([loadHealth(), loadUsers()]);
    } catch (error) {
      setUserStatus(error.message);
      setUserStatusError(true);
    }
  }

  async function handleSaveUser(event) {
    event.preventDefault();

    const payload = {
      ...userForm,
      profile_name: userForm.profile_name.trim().toLowerCase(),
      nome: userForm.nome.trim(),
      cargo_atual: userForm.cargo_atual.trim(),
      email: userForm.email.trim(),
      telefone: userForm.telefone.trim(),
      linkedin: userForm.linkedin.trim(),
      github: userForm.github.trim() || null,
      cidade: userForm.cidade.trim(),
      estado: userForm.estado.trim().toUpperCase(),
      experiencias: userForm.experiencias
        .map((item) => ({
          ...item,
          empresa: item.empresa.trim(),
          cargo: item.cargo.trim(),
          periodo: item.periodo.trim(),
          descricao: item.descricao.trim(),
          tecnologias: item.tecnologias.filter(Boolean),
          realizacoes: item.realizacoes.filter(Boolean)
        }))
        .filter((item) => item.empresa || item.cargo || item.descricao),
      educacao: userForm.educacao
        .map((item) => ({
          ...item,
          instituicao: item.instituicao.trim(),
          curso: item.curso.trim(),
          periodo: item.periodo.trim()
        }))
        .filter((item) => item.instituicao || item.curso),
      habilidades: userForm.habilidades.filter(Boolean),
      idiomas: userForm.idiomas
        .map((item) => ({
          ...item,
          idioma: item.idioma.trim(),
          nivel: item.nivel.trim()
        }))
        .filter((item) => item.idioma || item.nivel)
    };

    try {
      if (editingUserId) {
        await apiFetch(`/api/users/${editingUserId}`, {
          method: 'PUT',
          body: JSON.stringify(payload)
        });
        setUserStatus('Usuário atualizado com sucesso.');
      } else {
        await apiFetch('/api/users', {
          method: 'POST',
          body: JSON.stringify(payload)
        });
        setUserStatus('Usuário criado com sucesso.');
      }

      setUserStatusError(false);
      resetUserForm();
      await Promise.all([loadHealth(), loadUsers()]);
    } catch (error) {
      setUserStatus(error.message);
      setUserStatusError(true);
    }
  }

  function resetUserForm() {
    setEditingUserId(null);
    setUserForm({
      ...emptyUserForm,
      experiencias: [createExperience()],
      educacao: [createEducation()],
      habilidades: [],
      idiomas: []
    });
    setSkillInput('');
  }

  function updateUserField(field, value) {
    setUserForm((current) => ({ ...current, [field]: value }));
  }

  function updateListItem(section, index, field, value) {
    setUserForm((current) => ({
      ...current,
      [section]: current[section].map((item, itemIndex) =>
        itemIndex === index ? { ...item, [field]: value } : item
      )
    }));
  }

  function addListItem(section) {
    setUserForm((current) => ({
      ...current,
      [section]: [
        ...current[section],
        section === 'experiencias'
          ? createExperience()
          : section === 'educacao'
            ? createEducation()
            : createLanguage()
      ]
    }));
  }

  function removeListItem(section, index) {
    setUserForm((current) => {
      const nextItems = current[section].filter((_, itemIndex) => itemIndex !== index);
      return {
        ...current,
        [section]:
          nextItems.length > 0
            ? nextItems
            : section === 'experiencias'
              ? [createExperience()]
              : section === 'educacao'
                ? [createEducation()]
                : []
      };
    });
  }

  function addSkill() {
    const normalized = skillInput.trim();
    if (!normalized) {
      return;
    }

    setUserForm((current) => {
      if (current.habilidades.some((item) => item.toLowerCase() === normalized.toLowerCase())) {
        return current;
      }
      return {
        ...current,
        habilidades: [...current.habilidades, normalized]
      };
    });

    setSkillInput('');
  }

  function removeSkill(skill) {
    setUserForm((current) => ({
      ...current,
      habilidades: current.habilidades.filter((item) => item !== skill)
    }));
  }

  function renderResumePanel() {
    return (
      <section className={`panel tab-panel ${activeTab === 'resume' ? 'active' : ''}`}>
        <div className="panel-header">
          <div>
            <p className="panel-kicker">Geração de CV</p>
            <h2>Nova vaga e histórico</h2>
          </div>
          <button className="ghost-button" onClick={() => void Promise.all([loadHealth(), loadHistory(selectedJobId)])}>
            Atualizar dados
          </button>
        </div>

        <div className="resume-layout">
          <div className="card">
            <div className="card-header">
              <h3>Criar vaga</h3>
              <p>Cole a descrição da vaga e gere variantes com base no perfil ativo.</p>
            </div>

            <form className="form-stack" onSubmit={handleCreateJob}>
              <label>
                <span>Quantidade de CVs</span>
                <select value={variantCount} onChange={(event) => setVariantCount(Number(event.target.value))}>
                  {[1, 2, 3, 4, 5].map((value) => (
                    <option key={value} value={value}>
                      {value}
                    </option>
                  ))}
                </select>
              </label>

              <label>
                <span>Descrição da vaga</span>
                <textarea
                  rows={14}
                  value={jobContent}
                  onChange={(event) => setJobContent(event.target.value)}
                  placeholder="Cole aqui o texto da vaga."
                />
              </label>

              <button type="submit" className="primary-button">
                Criar vaga e gerar CVs
              </button>

              <p className={`form-status ${resumeStatus ? (resumeStatusError ? 'error-text' : 'success-text') : ''}`}>
                {resumeStatus}
              </p>
            </form>
          </div>

          <div className="card">
            <div className="card-header split">
              <div>
                <h3>Histórico</h3>
                <p>Selecione uma vaga para ver as variantes.</p>
              </div>
              <strong>{jobs.length}</strong>
            </div>

            <div className="history-list">
              {jobs.length === 0 ? (
                <EmptyState message="Nenhuma vaga criada ainda." />
              ) : (
                jobs.map((job) => (
                  <button
                    key={job.job_id}
                    type="button"
                    className={`history-item ${job.job_id === selectedJobId ? 'active' : ''}`}
                    onClick={() => {
                      setSelectedJobId(job.job_id);
                      void loadVariants(job.job_id);
                    }}
                  >
                    <div className="history-item-header">
                      <div>
                        <h4>{job.job_title}</h4>
                        <p>{job.company}</p>
                      </div>
                      <span className="score-pill">{job.best_score}</span>
                    </div>
                    <div className="meta-line">
                      <span>{job.variants_count} CV(s)</span>
                      <span>•</span>
                      <span>{formatDate(job.created_at)}</span>
                    </div>
                  </button>
                ))
              )}
            </div>
          </div>

          <div className="card">
            <div className="card-header split">
              <div>
                <h3>{selectedJob?.job_title || 'Nenhuma vaga selecionada'}</h3>
                <p>
                  {selectedJob
                    ? `${selectedJob.company} • ${selectedJob.variants_count} variante(s)`
                    : 'Escolha um item do histórico para gerenciar as variantes.'}
                </p>
              </div>

              <div className="actions-inline">
                <button className="ghost-button" onClick={handleGenerateMore} disabled={!selectedJob}>
                  Gerar mais
                </button>
                <button className="danger-button" onClick={handleDeleteJob} disabled={!selectedJob}>
                  Excluir vaga
                </button>
              </div>
            </div>

            <div className="variants-list">
              {!selectedJob ? (
                <EmptyState message="Selecione uma vaga para ver as variantes." />
              ) : variants.length === 0 ? (
                <EmptyState message="Nenhuma variante gerada para esta vaga." />
              ) : (
                variants.map((variant) => (
                  <article key={variant.id} className="variant-card">
                    <div className="variant-card-header">
                      <div>
                        <h4>Variante {variant.round}</h4>
                        <p>{variant.content?.cargo || '-'}</p>
                      </div>
                      <div className="actions-inline">
                        <span className={`status-pill ${statusClassName(variant.ats_status)}`}>
                          {variant.ats_status}
                        </span>
                        <span className="score-pill">{variant.ats_score}</span>
                      </div>
                    </div>

                    <p>{variant.content?.resumo || '-'}</p>

                    <div className="actions-group">
                      <button className="ghost-button small" onClick={() => setPreviewVariant(variant)}>
                        Prévia
                      </button>
                      <button className="ghost-button small" onClick={() => void handleDownloadVariant(variant.id)}>
                        Baixar DOCX
                      </button>
                      <button className="danger-button small" onClick={() => void handleDeleteVariant(variant.id)}>
                        Excluir
                      </button>
                    </div>
                  </article>
                ))
              )}
            </div>
          </div>
        </div>
      </section>
    );
  }

  function renderUsersPanel() {
    return (
      <section className={`panel tab-panel ${activeTab === 'users' ? 'active' : ''}`}>
        <div className="panel-header">
          <div>
            <p className="panel-kicker">Gerenciamento de Usuários</p>
            <h2>Perfis profissionais</h2>
          </div>
          <div className="actions-inline">
            <button className="ghost-button" onClick={() => void Promise.all([loadHealth(), loadUsers()])}>
              Atualizar dados
            </button>
            <button
              className="primary-button"
              onClick={() => {
                resetUserForm();
                setUserStatus('');
                setUserStatusError(false);
              }}
            >
              Novo usuário
            </button>
          </div>
        </div>

        <div className="users-layout">
          <div className="card">
            <div className="card-header split">
              <div>
                <h3>Perfis cadastrados</h3>
                <p>Ative, edite ou remova usuários.</p>
              </div>
              <strong>{users.length}</strong>
            </div>

            <div className="users-list">
              {users.length === 0 ? (
                <EmptyState message="Nenhum usuário cadastrado." />
              ) : (
                users.map((user) => {
                  const isActive = user.id === activeUserId;
                  return (
                    <article key={user.id} className={`user-card ${isActive ? 'active' : ''}`}>
                      <div className="user-card-header">
                        <div>
                          <h4>{user.nome}</h4>
                          <p>{user.cargo_atual}</p>
                        </div>
                        {isActive ? <span className="pill">Ativo</span> : null}
                      </div>

                      <p>{user.email}</p>

                      <div className="meta-line">
                        <span>
                          {user.cidade}, {user.estado}
                        </span>
                        <span>•</span>
                        <span>{user.experiencias.length} experiências</span>
                        <span>•</span>
                        <span>{user.habilidades.length} habilidades</span>
                      </div>

                      <div className="actions-group">
                        <button className="ghost-button small" onClick={() => void handleSetActiveUser(user.id)}>
                          {isActive ? 'Selecionado' : 'Ativar'}
                        </button>
                        <button className="ghost-button small" onClick={() => startEditingUser(user)}>
                          Editar
                        </button>
                        <button className="danger-button small" onClick={() => void handleDeleteUser(user)}>
                          Excluir
                        </button>
                      </div>
                    </article>
                  );
                })
              )}
            </div>
          </div>

          <div className="card">
            <div className="card-header">
              <h3>{editingUserId ? 'Editar usuário' : 'Novo usuário'}</h3>
              <p>Preencha o perfil usado como base para a geração de CV.</p>
            </div>

            <form className="form-stack" onSubmit={handleSaveUser}>
              <div className="two-columns">
                <Field label="Nome do perfil" value={userForm.profile_name} onChange={(value) => updateUserField('profile_name', value)} />
                <Field label="Nome completo" value={userForm.nome} onChange={(value) => updateUserField('nome', value)} />
                <Field label="Cargo atual" value={userForm.cargo_atual} onChange={(value) => updateUserField('cargo_atual', value)} />
                <Field label="Email" value={userForm.email} type="email" onChange={(value) => updateUserField('email', value)} />
                <Field label="Telefone" value={userForm.telefone} onChange={(value) => updateUserField('telefone', value)} />
                <Field label="LinkedIn" value={userForm.linkedin} onChange={(value) => updateUserField('linkedin', value)} />
                <Field label="GitHub" value={userForm.github} onChange={(value) => updateUserField('github', value)} />
                <Field label="Cidade" value={userForm.cidade} onChange={(value) => updateUserField('cidade', value)} />
                <Field label="Estado" value={userForm.estado} onChange={(value) => updateUserField('estado', value)} />
              </div>

              <div className="editor-section">
                <div className="section-title-row">
                  <h4>Experiências</h4>
                  <button type="button" className="ghost-button small" onClick={() => addListItem('experiencias')}>
                    Adicionar
                  </button>
                </div>

                <div className="dynamic-list">
                  {userForm.experiencias.map((experience, index) => (
                    <div key={`experience-${index}`} className="dynamic-card">
                      <div className="dynamic-card-header">
                        <strong>Experiência</strong>
                        <button type="button" className="icon-button" onClick={() => removeListItem('experiencias', index)}>
                          ×
                        </button>
                      </div>

                      <div className="two-columns">
                        <Field label="Empresa" value={experience.empresa} onChange={(value) => updateListItem('experiencias', index, 'empresa', value)} />
                        <Field label="Cargo" value={experience.cargo} onChange={(value) => updateListItem('experiencias', index, 'cargo', value)} />
                        <Field label="Período" value={experience.periodo} onChange={(value) => updateListItem('experiencias', index, 'periodo', value)} />
                        <Field
                          label="Tecnologias"
                          value={experience.tecnologias.join(', ')}
                          onChange={(value) => updateListItem('experiencias', index, 'tecnologias', splitCommaValues(value))}
                          placeholder="Python, FastAPI"
                        />
                      </div>

                      <Field
                        label="Descrição"
                        as="textarea"
                        rows={4}
                        value={experience.descricao}
                        onChange={(value) => updateListItem('experiencias', index, 'descricao', value)}
                      />

                      <Field
                        label="Realizações"
                        as="textarea"
                        rows={3}
                        value={experience.realizacoes.join('\n')}
                        onChange={(value) => updateListItem('experiencias', index, 'realizacoes', splitLineValues(value))}
                        placeholder="Uma por linha"
                      />
                    </div>
                  ))}
                </div>
              </div>

              <div className="editor-section">
                <div className="section-title-row">
                  <h4>Formação</h4>
                  <button type="button" className="ghost-button small" onClick={() => addListItem('educacao')}>
                    Adicionar
                  </button>
                </div>

                <div className="dynamic-list">
                  {userForm.educacao.map((education, index) => (
                    <div key={`education-${index}`} className="dynamic-card compact">
                      <div className="dynamic-card-header">
                        <strong>Formação</strong>
                        <button type="button" className="icon-button" onClick={() => removeListItem('educacao', index)}>
                          ×
                        </button>
                      </div>

                      <div className="two-columns">
                        <Field
                          label="Instituição"
                          value={education.instituicao}
                          onChange={(value) => updateListItem('educacao', index, 'instituicao', value)}
                        />
                        <Field label="Curso" value={education.curso} onChange={(value) => updateListItem('educacao', index, 'curso', value)} />
                        <Field label="Período" value={education.periodo} onChange={(value) => updateListItem('educacao', index, 'periodo', value)} />
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              <div className="editor-section">
                <div className="section-title-row">
                  <h4>Habilidades</h4>
                  <div className="skill-input-row">
                    <input
                      value={skillInput}
                      onChange={(event) => setSkillInput(event.target.value)}
                      onKeyDown={(event) => {
                        if (event.key === 'Enter') {
                          event.preventDefault();
                          addSkill();
                        }
                      }}
                      placeholder="Ex: Python"
                    />
                    <button type="button" className="ghost-button small" onClick={addSkill}>
                      Adicionar
                    </button>
                  </div>
                </div>

                <div className="tags-list">
                  {userForm.habilidades.length === 0 ? (
                    <EmptyState message="Nenhuma habilidade adicionada." />
                  ) : (
                    userForm.habilidades.map((skill) => (
                      <span key={skill} className="skill-tag">
                        {skill}
                        <button type="button" className="icon-button" onClick={() => removeSkill(skill)}>
                          ×
                        </button>
                      </span>
                    ))
                  )}
                </div>
              </div>

              <div className="editor-section">
                <div className="section-title-row">
                  <h4>Idiomas</h4>
                  <button type="button" className="ghost-button small" onClick={() => addListItem('idiomas')}>
                    Adicionar
                  </button>
                </div>

                <div className="dynamic-list">
                  {userForm.idiomas.length === 0 ? (
                    <EmptyState message="Nenhum idioma adicionado." />
                  ) : (
                    userForm.idiomas.map((language, index) => (
                      <div key={`language-${index}`} className="dynamic-card compact">
                        <div className="dynamic-card-header">
                          <strong>Idioma</strong>
                          <button type="button" className="icon-button" onClick={() => removeListItem('idiomas', index)}>
                            ×
                          </button>
                        </div>

                        <div className="two-columns">
                          <Field label="Idioma" value={language.idioma} onChange={(value) => updateListItem('idiomas', index, 'idioma', value)} />
                          <Field label="Nível" value={language.nivel} onChange={(value) => updateListItem('idiomas', index, 'nivel', value)} />
                        </div>
                      </div>
                    ))
                  )}
                </div>
              </div>

              <div className="actions-inline end">
                <button
                  type="button"
                  className="ghost-button"
                  onClick={() => {
                    resetUserForm();
                    setUserStatus('');
                    setUserStatusError(false);
                  }}
                >
                  Limpar
                </button>
                <button type="submit" className="primary-button">
                  {editingUserId ? 'Atualizar usuário' : 'Salvar usuário'}
                </button>
              </div>

              <p className={`form-status ${userStatus ? (userStatusError ? 'error-text' : 'success-text') : ''}`}>
                {userStatus}
              </p>
            </form>
          </div>
        </div>
      </section>
    );
  }

  return (
    <div className="app-shell">
      <header className="hero">
        <div>
          <p className="eyebrow">PassAI Simplificado</p>
          <h1>Frontend em React + Vite, com foco só em CV e usuários.</h1>
          <p className="hero-copy">
            O projeto agora fica com uma interface web simples, duas áreas funcionais e nenhuma dependência de áudio,
            chat ou captura multimodal.
          </p>
        </div>

        <div className="hero-stats">
          <div className="stat-card">
            <span className="stat-label">Backend</span>
            <strong className={health.online ? '' : 'error-text'}>{health.status}</strong>
          </div>
          <div className="stat-card">
            <span className="stat-label">Usuário ativo</span>
            <strong>{activeUser?.nome || 'Nenhum'}</strong>
          </div>
          <div className="stat-card">
            <span className="stat-label">Vagas no histórico</span>
            <strong>{jobs.length}</strong>
          </div>
        </div>
      </header>

      <nav className="tabs">
        <button className={`tab-button ${activeTab === 'resume' ? 'active' : ''}`} onClick={() => setActiveTab('resume')}>
          Gerar CV
        </button>
        <button className={`tab-button ${activeTab === 'users' ? 'active' : ''}`} onClick={() => setActiveTab('users')}>
          Usuários
        </button>
      </nav>

      <main className="content-grid">
        {renderResumePanel()}
        {renderUsersPanel()}
      </main>

      {previewVariant ? (
        <div className="preview-overlay" onClick={() => setPreviewVariant(null)}>
          <article className="preview-sheet" onClick={(event) => event.stopPropagation()}>
            <div className="preview-header">
              <div>
                <p className="panel-kicker">Pré-visualização</p>
                <h3>
                  {previewVariant.content?.nome || 'CV'} • Variante {previewVariant.round}
                </h3>
              </div>
              <button className="icon-button" onClick={() => setPreviewVariant(null)}>
                ×
              </button>
            </div>

            <div className="preview-body">
              <PreviewSection title="Resumo">
                <p>{previewVariant.content?.resumo || '-'}</p>
              </PreviewSection>

              <PreviewSection title="Contato">
                <p>
                  {previewVariant.content?.email || '-'} • {previewVariant.content?.telefone || '-'}
                </p>
                <p>{previewVariant.content?.linkedin || '-'}</p>
              </PreviewSection>

              <PreviewSection title="Habilidades">
                <p>{previewVariant.content?.habilidades?.join(', ') || '-'}</p>
              </PreviewSection>

              <PreviewSection title="Experiências">
                {previewVariant.content?.experiencias?.length ? (
                  previewVariant.content.experiencias.map((experience, index) => (
                    <article key={`${experience.empresa}-${index}`}>
                      <strong>
                        {experience.cargo || '-'} - {experience.empresa || '-'}
                      </strong>
                      <p>{experience.periodo || '-'}</p>
                      <p>{experience.descricao || '-'}</p>
                      {experience.realizacoes?.length ? (
                        <ul>
                          {experience.realizacoes.map((item, itemIndex) => (
                            <li key={`${experience.empresa}-${index}-${itemIndex}`}>{item}</li>
                          ))}
                        </ul>
                      ) : null}
                      {experience.tecnologias?.length ? (
                        <p>
                          <strong>Tecnologias:</strong> {experience.tecnologias.join(', ')}
                        </p>
                      ) : null}
                    </article>
                  ))
                ) : (
                  <p>-</p>
                )}
              </PreviewSection>

              <PreviewSection title="Formação">
                {previewVariant.content?.educacao?.length ? (
                  previewVariant.content.educacao.map((education, index) => (
                    <article key={`${education.instituicao}-${index}`}>
                      <strong>{education.curso || '-'}</strong>
                      <p>
                        {education.instituicao || '-'} • {education.periodo || '-'}
                      </p>
                    </article>
                  ))
                ) : (
                  <p>-</p>
                )}
              </PreviewSection>
            </div>
          </article>
        </div>
      ) : null}
    </div>
  );
}

function Field({ as = 'input', label, value, onChange, rows, type = 'text', placeholder = '' }) {
  return (
    <label>
      <span>{label}</span>
      {as === 'textarea' ? (
        <textarea rows={rows || 4} value={value} onChange={(event) => onChange(event.target.value)} placeholder={placeholder} />
      ) : (
        <input type={type} value={value} onChange={(event) => onChange(event.target.value)} placeholder={placeholder} />
      )}
    </label>
  );
}

function EmptyState({ message }) {
  return <div className="empty-state">{message}</div>;
}

function PreviewSection({ title, children }) {
  return (
    <section className="preview-section">
      <h4>{title}</h4>
      {children}
    </section>
  );
}

function formatDate(dateString) {
  try {
    return new Date(dateString).toLocaleString('pt-BR', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  } catch {
    return dateString;
  }
}

function splitCommaValues(value) {
  return value
    .split(',')
    .map((item) => item.trim())
    .filter(Boolean);
}

function splitLineValues(value) {
  return value
    .split('\n')
    .map((item) => item.trim())
    .filter(Boolean);
}

function statusClassName(status) {
  if (status === 'APPROVED') {
    return 'status-approved';
  }
  if (status === 'RISK') {
    return 'status-risk';
  }
  return 'status-rejected';
}

export default App;

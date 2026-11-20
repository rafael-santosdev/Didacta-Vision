/**
 * Didacta Vision - JavaScript Moderno & Interações AJAX
 * Suporte completo a Modais Bootstrap, Toasts flutuantes e operações sem reload
 */

(function () {
    'use strict';

    // 1. UTILITÁRIOS: CSRF TOKEN
    function getCsrfToken() {
        const meta = document.querySelector('meta[name="csrf-token"]');
        if (meta && meta.content) return meta.content;

        const input = document.querySelector('input[name="csrfmiddlewaretoken"]');
        if (input && input.value) return input.value;

        const cookieMatch = document.cookie.match(/csrftoken=([^;]+)/);
        return cookieMatch ? decodeURIComponent(cookieMatch[1]) : '';
    }

    // 2. UTILITÁRIOS: TOAST NOTIFICATIONS
    function dvToast(message, type = 'info', duration = 4000) {
        let container = document.getElementById('dvToastContainer');
        if (!container) {
            container = document.createElement('div');
            container.id = 'dvToastContainer';
            container.className = 'dv-toast-container';
            document.body.appendChild(container);
        }

        const iconClass = {
            success: 'bi-check-circle-fill text-success',
            error: 'bi-exclamation-octagon-fill text-danger',
            warning: 'bi-exclamation-triangle-fill text-warning',
            info: 'bi-info-circle-fill text-info'
        }[type] || 'bi-info-circle-fill text-info';

        const toast = document.createElement('div');
        toast.className = `dv-toast dv-toast--${type}`;
        toast.setAttribute('role', 'alert');
        toast.innerHTML = `
            <div class="dv-toast__icon"><i class="bi ${iconClass}"></i></div>
            <div class="dv-toast__body">${message}</div>
            <button type="button" class="dv-toast__close" aria-label="Fechar">&times;</button>
        `;

        container.appendChild(toast);

        // Animação de entrada
        requestAnimationFrame(() => {
            toast.classList.add('is-visible');
        });

        const close = () => {
            toast.classList.remove('is-visible');
            toast.addEventListener('transitionend', () => toast.remove(), { once: true });
        };

        toast.querySelector('.dv-toast__close').addEventListener('click', close);
        if (duration > 0) {
            setTimeout(close, duration);
        }
    }
    window.dvToast = dvToast;

    // Helper universal para requisições fetch com CSRF e cabeçalhos corretos
    function dvFetch(url, options = {}) {
        options.headers = options.headers || {};
        options.headers['X-Requested-With'] = 'XMLHttpRequest';
        options.headers['X-CSRFToken'] = getCsrfToken();
        return fetch(url, options);
    }
    window.dvFetch = dvFetch;

    const documentListenerHandlers = new Map();
    function addDocumentListener(key, eventName, handler) {
        const previous = documentListenerHandlers.get(key);
        if (previous) document.removeEventListener(previous.eventName, previous.handler);
        document.addEventListener(eventName, handler);
        documentListenerHandlers.set(key, { eventName, handler });
    }

    // Atualiza contadores numéricos nos badges da navbar
    function updateNavbarBadges(type, newCount) {
        if (type === 'notifications') {
            const badges = document.querySelectorAll('.dv-notification-badge--notifications');
            badges.forEach(b => {
                if (newCount > 0) {
                    b.textContent = newCount;
                    b.style.display = 'inline-flex';
                } else {
                    b.style.display = 'none';
                }
            });
        }
    }

    // 3. MODAL DINÂMICO UNIVERSAL
    function getDynamicModal() {
        let modalEl = document.getElementById('dvDynamicModal');
        if (!modalEl) {
            modalEl = document.createElement('div');
            modalEl.id = 'dvDynamicModal';
            modalEl.className = 'modal fade';
            modalEl.setAttribute('tabindex', '-1');
            modalEl.setAttribute('aria-hidden', 'true');
            modalEl.innerHTML = `
                <div class="modal-dialog modal-dialog-centered">
                    <div class="modal-content dv-modal-content">
                        <div class="modal-header dv-modal-header">
                            <h5 class="modal-title dv-modal-title" id="dvDynamicModalTitle"></h5>
                            <button type="button" class="btn-close btn-close-white" data-bs-dismiss="modal" aria-label="Fechar"></button>
                        </div>
                        <div class="modal-body dv-modal-body" id="dvDynamicModalBody"></div>
                    </div>
                </div>
            `;
            document.body.appendChild(modalEl);
        }
        return modalEl;
    }

    function showConfirmModal({ title, body, confirmText = 'Confirmar', cancelText = 'Cancelar', isDanger = false, onConfirm }) {
        const modalEl = getDynamicModal();
        const titleEl = modalEl.querySelector('#dvDynamicModalTitle');
        const bodyEl = modalEl.querySelector('#dvDynamicModalBody');

        titleEl.textContent = title;
        bodyEl.innerHTML = `
            <div style="font-size:0.95rem; line-height:1.6; margin-bottom:20px;">${body}</div>
            <div class="d-flex justify-content-end gap-2">
                <button type="button" class="dv-btn ghost" data-bs-dismiss="modal">${cancelText}</button>
                <button type="button" class="dv-btn ${isDanger ? 'danger' : 'primary'}" id="dvModalConfirmActionBtn">
                    ${confirmText}
                </button>
            </div>
        `;

        const bsModal = bootstrap.Modal.getOrCreateInstance(modalEl);
        bsModal.show();

        const confirmBtn = bodyEl.querySelector('#dvModalConfirmActionBtn');
        const clickHandler = async () => {
            confirmBtn.disabled = true;
            confirmBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-1"></span> Aguarde...';
            try {
                await onConfirm(bsModal);
            } finally {
                confirmBtn.removeEventListener('click', clickHandler);
            }
        };
        confirmBtn.addEventListener('click', clickHandler);
    }

    // 4. RESERVA DE VAGAS VIA AJAX
    function initReservations() {
        addDocumentListener('reservation-click', 'click', async (e) => {
            const btn = e.target.closest('.js-btn-reservar');
            if (!btn) return;

            e.preventDefault();
            const sessionId = btn.getAttribute('data-session-id');
            const reserveUrl = btn.getAttribute('data-url') || btn.getAttribute('href');
            const filmTitle = btn.getAttribute('data-film-title') || 'este filme';
            const sessionDate = btn.getAttribute('data-session-date') || '';
            const sessionLocal = btn.getAttribute('data-session-local') || '';

            showConfirmModal({
                title: 'Confirmar Reserva',
                body: `
                    <p>Deseja confirmar sua reserva para a sessão:</p>
                    <div class="p-3 my-2 rounded" style="background:rgba(255,255,255,0.05);border:1px solid rgba(255,255,255,0.1);">
                        <strong style="color:hsl(var(--foreground));">${filmTitle}</strong><br>
                        ${sessionDate ? `<small class="text-muted"><i class="bi bi-calendar3 me-1"></i> ${sessionDate}</small><br>` : ''}
                        ${sessionLocal ? `<small class="text-muted"><i class="bi bi-geo-alt me-1"></i> ${sessionLocal}</small>` : ''}
                    </div>
                    <small class="text-muted">Você poderá cancelar a qualquer momento antes do início da sessão.</small>
                `,
                confirmText: '<i class="bi bi-calendar-check me-1"></i> Confirmar vaga',
                onConfirm: async (bsModal) => {
                    try {
                        const formData = new FormData();
                        formData.append('sessao', sessionId);

                        const res = await dvFetch(reserveUrl, {
                            method: 'POST',
                            body: formData
                        });
                        const data = await res.json();

                        if (res.ok && data.success) {
                            bsModal.hide();
                            dvToast(data.message || 'Reserva confirmada com sucesso!', 'success');

                            // Atualiza os botões da sessão na página
                            const cancelUrl = `/reservations/${data.reserva_id}/cancel/`;
                            btn.className = 'dv-btn ghost js-btn-cancelar-reserva';
                            btn.setAttribute('data-url', cancelUrl);
                            btn.setAttribute('href', cancelUrl);
                            btn.setAttribute('data-reserva-id', data.reserva_id);
                            btn.innerHTML = '<i class="bi bi-x-circle me-1"></i> Cancelar Reserva';

                            // Atualiza contagem de vagas visualmente se houver elemento
                            const vagasEl = document.querySelector(`.js-vagas-count-${sessionId}`);
                            if (vagasEl && typeof data.vagas_disponiveis !== 'undefined') {
                                vagasEl.textContent = `${data.vagas_disponiveis} vagas`;
                            }
                        } else {
                            dvToast(data.message || 'Erro ao realizar reserva.', 'error');
                            bsModal.hide();
                        }
                    } catch (err) {
                        console.error('Erro ao reservar:', err);
                        dvToast('Não foi possível realizar a reserva. Tente novamente.', 'error');
                        bsModal.hide();
                    }
                }
            });
        });
    }

    // 5. CANCELAMENTO DE RESERVA VIA AJAX
    function initCancelReservations() {
        addDocumentListener('reservation-cancel-click', 'click', async (e) => {
            const btn = e.target.closest('.js-btn-cancelar-reserva');
            if (!btn) return;

            e.preventDefault();
            const cancelUrl = btn.getAttribute('data-url') || btn.getAttribute('href');
            const filmTitle = btn.getAttribute('data-film-title') || 'esta sessão';
            const reservaRow = btn.closest('tr') || btn.closest('.dv-reservation-card');

            const modalEl = getDynamicModal();
            const titleEl = modalEl.querySelector('#dvDynamicModalTitle');
            const bodyEl = modalEl.querySelector('#dvDynamicModalBody');

            titleEl.textContent = 'Cancelar Reserva';
            bodyEl.innerHTML = `
                <p>Tem certeza que deseja cancelar sua reserva para <strong>${filmTitle}</strong>?</p>
                <div class="dv-form-group my-3">
                    <label for="dvCancelJustificativa" class="form-label" style="font-size:0.85rem;">Justificativa (opcional):</label>
                    <textarea id="dvCancelJustificativa" class="form-control" rows="3" placeholder="Informe o motivo do cancelamento se desejar..."></textarea>
                </div>
                <div class="d-flex justify-content-end gap-2">
                    <button type="button" class="dv-btn ghost" data-bs-dismiss="modal">Manter Reserva</button>
                    <button type="button" class="dv-btn danger" id="dvConfirmCancelBtn">
                        <i class="bi bi-x-circle me-1"></i> Cancelar Reserva
                    </button>
                </div>
            `;

            const bsModal = bootstrap.Modal.getOrCreateInstance(modalEl);
            bsModal.show();

            const confirmBtn = bodyEl.querySelector('#dvConfirmCancelBtn');
            confirmBtn.addEventListener('click', async () => {
                confirmBtn.disabled = true;
                confirmBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-1"></span> Cancelando...';

                try {
                    const justificativa = bodyEl.querySelector('#dvCancelJustificativa').value.trim();
                    const formData = new FormData();
                    formData.append('justificativa', justificativa);

                    const res = await dvFetch(cancelUrl, {
                        method: 'POST',
                        body: formData
                    });
                    const data = await res.json();

                    if (res.ok && data.success) {
                        bsModal.hide();
                        dvToast(data.message || 'Reserva cancelada com sucesso!', 'success');

                        // Se estiver na lista de reservas
                        if (reservaRow) {
                            reservaRow.style.transition = 'opacity 0.3s, transform 0.3s';
                            reservaRow.style.opacity = '0';
                            reservaRow.style.transform = 'scale(0.95)';
                            setTimeout(() => reservaRow.remove(), 320);
                        } else {
                            // Se estiver na página do filme, volta o botão para "Reservar"
                            const sessionId = btn.getAttribute('data-session-id');
                            btn.className = 'dv-btn primary js-btn-reservar';
                            btn.setAttribute('data-url', `/reservations/create/${sessionId}/`);
                            btn.setAttribute('href', `/reservations/create/${sessionId}/`);
                            btn.innerHTML = '<i class="bi bi-calendar-plus me-1"></i> Reservar';

                            const vagasEl = document.querySelector(`.js-vagas-count-${sessionId}`);
                            if (vagasEl && typeof data.vagas_disponiveis !== 'undefined') {
                                vagasEl.textContent = `${data.vagas_disponiveis} vagas`;
                            }
                        }
                    } else {
                        dvToast(data.message || 'Erro ao cancelar reserva.', 'error');
                        bsModal.hide();
                    }
                } catch (err) {
                    console.error('Erro ao cancelar reserva:', err);
                    dvToast('Erro de comunicação. Tente novamente.', 'error');
                    bsModal.hide();
                }
            });
        });
    }

    // 6. MARCAÇÃO DE PRESENÇA ADMIN VIA AJAX
    function initPresenceAdmin() {
        addDocumentListener('presence-change', 'change', async (e) => {
            const select = e.target.closest('.js-presence-select');
            if (!select) return;

            const url = select.getAttribute('data-url') || (select.form ? select.form.action : null);
            if (!url) return;

            const newStatus = select.value;
            const statusCell = select.closest('tr') ? select.closest('tr').querySelector('.js-status-badge') : null;

            try {
                select.disabled = true;
                const formData = new FormData();
                formData.append('status', newStatus);

                const res = await dvFetch(url, {
                    method: 'POST',
                    body: formData
                });
                const data = await res.json();

                if (res.ok && data.success) {
                    dvToast(data.message || 'Status atualizado com sucesso!', 'success');
                    if (statusCell) {
                        statusCell.className = `dv-status ${data.badge_class || 'neutral'} js-status-badge`;
                        statusCell.textContent = data.status_display;
                    }
                } else {
                    dvToast(data.message || 'Erro ao atualizar presença.', 'error');
                }
            } catch (err) {
                console.error('Erro na chamada de presença:', err);
                dvToast('Erro ao atualizar presença. Tente novamente.', 'error');
            } finally {
                select.disabled = false;
            }
        });
    }

    // 7. FÓRUM: COMENTÁRIOS E RESPOSTAS VIA AJAX
    function initForum() {
        const commentForm = document.getElementById('dvForumCommentForm');
        if (commentForm) {
            commentForm.addEventListener('submit', async (e) => {
                e.preventDefault();
                const textarea = commentForm.querySelector('textarea[name="texto"]');
                const submitBtn = commentForm.querySelector('button[type="submit"]');
                const text = textarea ? textarea.value.trim() : '';

                if (text.length < 10) {
                    dvToast('O comentário deve ter no mínimo 10 caracteres.', 'warning');
                    textarea.focus();
                    return;
                }

                submitBtn.disabled = true;
                submitBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-1"></span> Publicando...';

                try {
                    const formData = new FormData(commentForm);
                    const res = await dvFetch(commentForm.action, {
                        method: 'POST',
                        body: formData
                    });
                    const data = await res.json();

                    if (res.ok && data.success) {
                        dvToast(data.message || 'Comentário publicado com sucesso!', 'success');
                        textarea.value = '';

                        // Inserir o comentário dinamicamente no DOM
                        const commentsList = document.getElementById('dvForumCommentsList');
                        const emptyBox = document.getElementById('dvForumEmptyState');
                        if (emptyBox) emptyBox.style.display = 'none';

                        if (commentsList && data.comment) {
                            const c = data.comment;
                            const commentArticle = document.createElement('article');
                            commentArticle.className = 'dv-comment dv-comment--new animate-in';
                            commentArticle.id = `comment-${c.id}`;
                            commentArticle.innerHTML = `
                                <div class="dv-comment__header">
                                    <div class="dv-comment__meta">
                                        <div class="dv-user-avatar-sm">
                                            ${c.foto_url ? `<img src="${c.foto_url}" alt="${c.autor}">` : '<i class="bi bi-person"></i>'}
                                        </div>
                                        <div>
                                            <strong>${c.autor}</strong>
                                            <span class="dv-tag ms-1">${c.tipo_usuario}</span>
                                            <small class="text-muted ms-2">${c.created_at}</small>
                                        </div>
                                    </div>
                                    <div class="dv-comment__actions">
                                        <button type="button" class="dv-btn ghost sm js-btn-delete-comment" data-url="${c.delete_url}" title="Excluir">
                                            <i class="bi bi-trash"></i>
                                        </button>
                                    </div>
                                </div>
                                <p class="dv-comment__text">${c.texto}</p>
                            `;
                            commentsList.prepend(commentArticle);
                        }
                    } else {
                        dvToast(data.message || 'Erro ao publicar comentário.', 'error');
                    }
                } catch (err) {
                    console.error('Erro ao enviar comentário:', err);
                    dvToast('Erro de comunicação. Tente novamente.', 'error');
                } finally {
                    submitBtn.disabled = false;
                    submitBtn.innerHTML = '<i class="bi bi-send me-1"></i> Publicar comentário';
                }
            });
        }

        // Excluir comentário via AJAX
        addDocumentListener('forum-delete-click', 'click', async (e) => {
            const btn = e.target.closest('.js-btn-delete-comment');
            if (!btn) return;

            e.preventDefault();
            const deleteUrl = btn.getAttribute('data-url') || btn.getAttribute('href');
            const commentEl = btn.closest('.dv-comment');

            showConfirmModal({
                title: 'Excluir Comentário',
                body: 'Tem certeza que deseja remover este comentário? Esta ação não pode ser desfeita.',
                confirmText: '<i class="bi bi-trash me-1"></i> Excluir',
                isDanger: true,
                onConfirm: async (bsModal) => {
                    try {
                        const res = await dvFetch(deleteUrl, { method: 'POST' });
                        const data = await res.json();

                        if (res.ok && data.success) {
                            bsModal.hide();
                            dvToast(data.message || 'Comentário removido.', 'success');
                            if (commentEl) {
                                commentEl.style.transition = 'opacity 0.25s, transform 0.25s';
                                commentEl.style.opacity = '0';
                                commentEl.style.transform = 'translateY(-10px)';
                                setTimeout(() => commentEl.remove(), 260);
                            }
                        } else {
                            dvToast(data.message || 'Erro ao excluir comentário.', 'error');
                            bsModal.hide();
                        }
                    } catch (err) {
                        console.error('Erro:', err);
                        dvToast('Erro ao excluir comentário.', 'error');
                        bsModal.hide();
                    }
                }
            });
        });
    }

    // 8. NOTIFICAÇÕES VIA AJAX
    function initNotifications() {
        // Marcar uma como lida
        addDocumentListener('notification-mark-read', 'click', async (e) => {
            const btn = e.target.closest('.js-btn-mark-read');
            if (!btn) return;

            e.preventDefault();
            const url = btn.getAttribute('data-url') || btn.getAttribute('href');
            const card = btn.closest('.dv-notification');

            try {
                btn.disabled = true;
                const res = await dvFetch(url, { method: 'POST' });
                const data = await res.json();

                if (res.ok && data.success) {
                    if (card) {
                        card.classList.remove('is-unread');
                        card.classList.add('is-read');
                        btn.outerHTML = '<span class="dv-status neutral"><i class="bi bi-check2"></i> Lida</span>';
                        const newBadge = card.querySelector('.dv-status.info');
                        if (newBadge) newBadge.remove();
                    }
                    if (typeof data.unread_count !== 'undefined') {
                        updateNavbarBadges('notifications', data.unread_count);
                    }
                    dvToast('Notificação marcada como lida.', 'info', 2000);
                }
            } catch (err) {
                console.error('Erro ao marcar notificação:', err);
            } finally {
                btn.disabled = false;
            }
        });

        // Marcar todas como lidas
        const markAllBtn = document.getElementById('dvMarkAllNotificationsBtn');
        if (markAllBtn) {
            markAllBtn.addEventListener('click', async (e) => {
                e.preventDefault();
                const url = markAllBtn.getAttribute('href') || markAllBtn.getAttribute('data-url');
                try {
                    markAllBtn.disabled = true;
                    markAllBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-1"></span> Marcando...';

                    const res = await dvFetch(url, { method: 'POST' });
                    const data = await res.json();

                    if (res.ok && data.success) {
                        dvToast(data.message || 'Todas as notificações marcadas como lidas.', 'success');
                        document.querySelectorAll('.dv-notification.is-unread').forEach(card => {
                            card.classList.remove('is-unread');
                            card.classList.add('is-read');
                            const btn = card.querySelector('.js-btn-mark-read');
                            if (btn) btn.outerHTML = '<span class="dv-status neutral"><i class="bi bi-check2"></i> Lida</span>';
                            const newBadge = card.querySelector('.dv-status.info');
                            if (newBadge) newBadge.remove();
                        });
                        updateNavbarBadges('notifications', 0);
                        markAllBtn.remove();
                    }
                } catch (err) {
                    console.error('Erro ao marcar todas:', err);
                }
            });
        }
    }

    // 9. MODAIS DE ADMINISTRAÇÃO: SESSÕES E FILMES
    function initAdminModals() {
        // Modal de Sessão (Criar / Editar)
        const sessionModalEl = document.getElementById('sessionModal');
        if (sessionModalEl) {
            const bsSessionModal = bootstrap.Modal.getOrCreateInstance(sessionModalEl);
            const modalBody = sessionModalEl.querySelector('#sessionModalBody');
            const modalTitle = sessionModalEl.querySelector('#sessionModalTitle');

            // Abrir para Criar Sessão
            addDocumentListener('session-create-click', 'click', async (e) => {
                const btn = e.target.closest('.js-session-create');
                if (!btn) return;
                e.preventDefault();

                const url = btn.getAttribute('data-url') || '/admin/sessions/ajax/create/';
                if (modalTitle) modalTitle.textContent = 'Nova Sessão';
                if (modalBody) modalBody.innerHTML = '<div class="text-center p-4"><span class="spinner-border text-primary"></span><p class="mt-2 text-muted">Carregando formulário...</p></div>';
                bsSessionModal.show();

                try {
                    const res = await dvFetch(url);
                    const html = await res.text();
                    modalBody.innerHTML = html;
                } catch (err) {
                    modalBody.innerHTML = '<div class="alert alert-danger">Erro ao carregar formulário.</div>';
                }
            });

            // Abrir para Editar Sessão
            addDocumentListener('session-edit-click', 'click', async (e) => {
                const btn = e.target.closest('.js-session-edit');
                if (!btn) return;
                e.preventDefault();

                const url = btn.getAttribute('data-edit-url') || btn.getAttribute('href');
                if (modalTitle) modalTitle.textContent = 'Editar Sessão';
                if (modalBody) modalBody.innerHTML = '<div class="text-center p-4"><span class="spinner-border text-primary"></span><p class="mt-2 text-muted">Carregando dados da sessão...</p></div>';
                bsSessionModal.show();

                try {
                    const res = await dvFetch(url);
                    const html = await res.text();
                    modalBody.innerHTML = html;
                } catch (err) {
                    modalBody.innerHTML = '<div class="alert alert-danger">Erro ao carregar sessão.</div>';
                }
            });

            // Submissão do Formulário de Sessão no Modal
            sessionModalEl.addEventListener('submit', async (e) => {
                const form = e.target.closest('#ajax-session-form');
                if (!form) return;

                e.preventDefault();
                const actionUrl = form.getAttribute('data-action-url') || form.action;
                const submitBtn = form.querySelector('button[type="submit"]');

                if (submitBtn) {
                    submitBtn.disabled = true;
                    submitBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-1"></span> Salvando...';
                }

                try {
                    const formData = new FormData(form);
                    const res = await dvFetch(actionUrl, {
                        method: 'POST',
                        body: formData
                    });
                    const data = await res.json();

                    if (res.ok && data.success) {
                        bsSessionModal.hide();
                        dvToast(data.message || 'Sessão salva com sucesso!', 'success');
                        setTimeout(() => requestPage(window.location.href, {
                            historyMode: 'replace',
                            restoreScroll: { x: window.scrollX, y: window.scrollY }
                        }), 600);
                    } else {
                        if (data.form_html) {
                            modalBody.innerHTML = data.form_html;
                        } else {
                            dvToast(data.message || 'Erro ao salvar sessão.', 'error');
                        }
                    }
                } catch (err) {
                    console.error('Erro ao salvar sessão:', err);
                    dvToast('Erro de comunicação.', 'error');
                } finally {
                    if (submitBtn) {
                        submitBtn.disabled = false;
                        submitBtn.innerHTML = '<i class="bi bi-check-circle"></i> Salvar alterações';
                    }
                }
            });
        }

        // Excluir Sessão via AJAX com confirmação
        addDocumentListener('session-delete-click', 'click', (e) => {
            const btn = e.target.closest('.js-session-delete');
            if (!btn) return;
            e.preventDefault();

            const deleteUrl = btn.getAttribute('data-delete-url') || btn.getAttribute('href');
            const row = btn.closest('tr');

            showConfirmModal({
                title: 'Excluir Sessão',
                body: 'Tem certeza que deseja excluir esta sessão? Todas as reservas vinculadas serão canceladas e os inscritos serão notificados.',
                confirmText: '<i class="bi bi-trash me-1"></i> Excluir Sessão',
                isDanger: true,
                onConfirm: async (bsModal) => {
                    try {
                        const res = await dvFetch(deleteUrl, { method: 'POST' });
                        const data = await res.json();
                        if (res.ok && data.success) {
                            bsModal.hide();
                            dvToast(data.message || 'Sessão excluída com sucesso!', 'success');
                            if (row) {
                                row.style.transition = 'opacity 0.25s, transform 0.25s';
                                row.style.opacity = '0';
                                row.style.transform = 'scale(0.95)';
                                setTimeout(() => row.remove(), 260);
                            }
                        } else {
                            dvToast(data.message || 'Erro ao excluir sessão.', 'error');
                            bsModal.hide();
                        }
                    } catch (err) {
                        console.error('Erro ao excluir:', err);
                        dvToast('Erro de conexão ao excluir.', 'error');
                        bsModal.hide();
                    }
                }
            });
        });

        // Modal de Filme (Criar / Editar)
        const filmModalEl = document.getElementById('filmModal');
        if (filmModalEl) {
            const bsFilmModal = bootstrap.Modal.getOrCreateInstance(filmModalEl);
            const modalBody = filmModalEl.querySelector('#filmModalBody');
            const modalTitle = filmModalEl.querySelector('#filmModalTitle');

            addDocumentListener('film-modal-trigger-click', 'click', async (e) => {
                const btn = e.target.closest('.js-film-modal-trigger');
                if (!btn) return;
                e.preventDefault();

                const url = btn.getAttribute('data-url') || btn.getAttribute('href');
                const isEdit = btn.classList.contains('js-film-edit');
                if (modalTitle) modalTitle.textContent = isEdit ? 'Editar Filme' : 'Cadastrar Novo Filme';
                if (modalBody) modalBody.innerHTML = '<div class="text-center p-4"><span class="spinner-border text-primary"></span><p class="mt-2 text-muted">Carregando formulário...</p></div>';
                bsFilmModal.show();

                try {
                    const res = await dvFetch(url);
                    const html = await res.text();
                    modalBody.innerHTML = html;
                } catch (err) {
                    modalBody.innerHTML = '<div class="alert alert-danger">Erro ao carregar dados do filme.</div>';
                }
            });

            filmModalEl.addEventListener('submit', async (e) => {
                const form = e.target.closest('#ajax-film-form');
                if (!form) return;

                e.preventDefault();
                const actionUrl = form.getAttribute('data-action-url') || form.action;
                const submitBtn = form.querySelector('button[type="submit"]');

                if (submitBtn) {
                    submitBtn.disabled = true;
                    submitBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-1"></span> Salvando...';
                }

                try {
                    const formData = new FormData(form);
                    const res = await dvFetch(actionUrl, {
                        method: 'POST',
                        body: formData
                    });
                    const data = await res.json();

                    if (res.ok && data.success) {
                        bsFilmModal.hide();
                        dvToast(data.message || 'Filme salvo com sucesso!', 'success');
                        setTimeout(() => requestPage(window.location.href, {
                            historyMode: 'replace',
                            restoreScroll: { x: window.scrollX, y: window.scrollY }
                        }), 600);
                    } else {
                        if (data.form_html) {
                            modalBody.innerHTML = data.form_html;
                        } else {
                            dvToast(data.message || 'Erro ao salvar filme.', 'error');
                        }
                    }
                } catch (err) {
                    console.error('Erro ao salvar filme:', err);
                    dvToast('Erro de comunicação.', 'error');
                } finally {
                    if (submitBtn) {
                        submitBtn.disabled = false;
                        submitBtn.innerHTML = '<i class="bi bi-check-circle"></i> Salvar alterações';
                    }
                }
            });
        }

        // Excluir Filme via AJAX com confirmação
        addDocumentListener('film-delete-click', 'click', (e) => {
            const btn = e.target.closest('.js-film-delete');
            if (!btn) return;
            e.preventDefault();

            const deleteUrl = btn.getAttribute('data-delete-url') || btn.getAttribute('href');
            const filmTitle = btn.getAttribute('data-film-title') || 'este filme';
            const row = btn.closest('tr');

            showConfirmModal({
                title: 'Excluir Filme',
                body: `Tem certeza que deseja excluir o filme <strong>${filmTitle}</strong>? Filmes com sessões ativas ou comentários não poderão ser excluídos.`,
                confirmText: '<i class="bi bi-trash me-1"></i> Excluir Filme',
                isDanger: true,
                onConfirm: async (bsModal) => {
                    try {
                        const res = await dvFetch(deleteUrl, { method: 'POST' });
                        const data = await res.json();
                        if (res.ok && data.success) {
                            bsModal.hide();
                            dvToast(data.message || 'Filme excluído com sucesso!', 'success');
                            if (row) {
                                row.style.transition = 'opacity 0.25s, transform 0.25s';
                                row.style.opacity = '0';
                                row.style.transform = 'scale(0.95)';
                                setTimeout(() => row.remove(), 260);
                            }
                        } else {
                            dvToast(data.message || 'Não foi possível excluir o filme.', 'error');
                            bsModal.hide();
                        }
                    } catch (err) {
                        console.error('Erro ao excluir:', err);
                        dvToast('Erro ao excluir filme.', 'error');
                        bsModal.hide();
                    }
                }
            });
        });
    }

    // 10. MODAL DE TRAILER DO YOUTUBE
    function initTrailerModal() {
        function getYouTubeId(url) {
            if (!url) return null;
            const regExp = /^.*(youtu.be\/|v\/|u\/\w\/|embed\/|watch\?v=|&v=)([^#&?]*).*/;
            const match = url.match(regExp);
            return (match && match[2].length === 11) ? match[2] : null;
        }

        addDocumentListener('trailer-click', 'click', (e) => {
            const trigger = e.target.closest('.js-open-trailer');
            if (!trigger) return;

            e.preventDefault();
            const trailerUrl = trigger.getAttribute('data-trailer-url') || trigger.getAttribute('href');
            const filmTitle = trigger.getAttribute('data-film-title') || 'Trailer do Filme';
            const videoId = getYouTubeId(trailerUrl);

            if (!videoId) {
                // Se não conseguir extrair o ID, abre diretamente em nova aba
                window.open(trailerUrl, '_blank', 'noreferrer');
                return;
            }

            let trailerModalEl = document.getElementById('dvTrailerModal');
            if (!trailerModalEl) {
                trailerModalEl = document.createElement('div');
                trailerModalEl.id = 'dvTrailerModal';
                trailerModalEl.className = 'modal fade';
                trailerModalEl.setAttribute('tabindex', '-1');
                trailerModalEl.innerHTML = `
                    <div class="modal-dialog modal-dialog-centered modal-lg">
                        <div class="modal-content dv-modal-content" style="background:#05050c;border:1px solid rgba(255,255,255,0.15);">
                            <div class="modal-header dv-modal-header" style="border-bottom:1px solid rgba(255,255,255,0.08);">
                                <h5 class="modal-title" id="dvTrailerModalTitle" style="font-size:1.05rem;"></h5>
                                <button type="button" class="btn-close btn-close-white" data-bs-dismiss="modal" aria-label="Fechar"></button>
                            </div>
                            <div class="modal-body p-0" style="background:#000;">
                                <div class="ratio ratio-16x9" id="dvTrailerPlayerContainer"></div>
                            </div>
                        </div>
                    </div>
                `;
                document.body.appendChild(trailerModalEl);

                // Ao fechar, limpa o iframe para parar o som
                trailerModalEl.addEventListener('hidden.bs.modal', () => {
                    const container = trailerModalEl.querySelector('#dvTrailerPlayerContainer');
                    if (container) container.innerHTML = '';
                });
            }

            trailerModalEl.querySelector('#dvTrailerModalTitle').textContent = filmTitle;
            const container = trailerModalEl.querySelector('#dvTrailerPlayerContainer');
            container.innerHTML = `
                <iframe src="https://www.youtube.com/embed/${videoId}?autoplay=1&rel=0" 
                        title="${filmTitle}" 
                        frameborder="0" 
                        allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture" 
                        allowfullscreen>
                </iframe>
            `;

            const bsTrailerModal = bootstrap.Modal.getOrCreateInstance(trailerModalEl);
            bsTrailerModal.show();
        });
    }

    // 11. FILTROS RÁPIDOS E BUSCA INSTANTÂNEA NO CATÁLOGO
    function initCatalogFilter() {
        const filterPills = document.querySelectorAll('.js-filter-pill');
        const searchInput = document.getElementById('dvCatalogSearch');
        const cards = document.querySelectorAll('.js-film-card');

        if (cards.length === 0) return;

        let activeGenre = '';
        let searchQuery = '';

        function applyFilters() {
            const query = searchQuery.trim().toLowerCase();
            cards.forEach(card => {
                const title = (card.getAttribute('data-title') || '').toLowerCase();
                const genre = (card.getAttribute('data-genre') || '').toLowerCase();
                const tema = (card.getAttribute('data-tema') || '').toLowerCase();
                const genres = genre.split('/').map(value => value.trim());

                const matchesGenre = !activeGenre || genre === activeGenre || genres.includes(activeGenre) || tema === activeGenre;
                const matchesSearch = !query || title.includes(query) || genre.includes(query) || tema.includes(query);

                card.classList.toggle('is-filtered-out', !matchesGenre || !matchesSearch);
            });

            // Exibe mensagem caso nenhum filme passe pelo filtro
            const visibleCards = Array.from(cards).filter(c => !c.classList.contains('is-filtered-out'));
            const emptyNotice = document.getElementById('dvCatalogNoResults');
            if (emptyNotice) {
                emptyNotice.style.display = visibleCards.length === 0 ? 'block' : 'none';
            }
        }

        if (searchInput) {
            searchInput.addEventListener('input', (e) => {
                searchQuery = e.target.value;
                applyFilters();
            });
        }

        filterPills.forEach(pill => {
            pill.addEventListener('click', (e) => {
                e.preventDefault();
                filterPills.forEach(p => p.classList.remove('is-active'));
                pill.classList.add('is-active');

                activeGenre = (pill.getAttribute('data-filter') || '').toLowerCase();
                applyFilters();
            });
        });
    }

    // 12. FECHAMENTO INTELIGENTE DO MENU MOBILE EM LINKS ÂNCORA
    function initMobileMenu() {
        const offcanvasEl = document.getElementById('dvMobileMenu');
        if (!offcanvasEl) return;
        const links = offcanvasEl.querySelectorAll('a[href*="#"]');
        links.forEach(link => {
            link.addEventListener('click', () => {
                const bsOffcanvas = bootstrap.Offcanvas.getInstance(offcanvasEl);
                if (bsOffcanvas) {
                    bsOffcanvas.hide();
                }
            });
        });
    }

    let latestPageRequest = 0;
    function renderFetchedPage(response, requestedUrl, options, requestId) {
        return response.text().then(html => {
            if (requestId !== latestPageRequest) return;
            const nextDocument = new DOMParser().parseFromString(html, 'text/html');
            if (!nextDocument.querySelector('main.dv-main')) {
                throw new Error('A resposta não contém uma página Didacta válida.');
            }

            const nextBodyNodes = Array.from(nextDocument.body.childNodes)
                .filter(node => node.nodeName.toLowerCase() !== 'script')
                .map(node => document.importNode(node, true));
            const activeScripts = Array.from(document.body.querySelectorAll('script'));

            document.body.className = nextDocument.body.className;
            document.body.replaceChildren(...nextBodyNodes, ...activeScripts);
            document.documentElement.lang = nextDocument.documentElement.lang;
            document.documentElement.dataset.bsTheme = nextDocument.documentElement.dataset.bsTheme || '';

            const nextTitle = nextDocument.querySelector('title');
            if (nextTitle) document.title = nextTitle.textContent;

            const currentCsrfMeta = document.querySelector('meta[name="csrf-token"]');
            const nextCsrfMeta = nextDocument.querySelector('meta[name="csrf-token"]');
            if (currentCsrfMeta && nextCsrfMeta) {
                currentCsrfMeta.content = nextCsrfMeta.content;
            }

            const finalUrl = new URL(response.url || requestedUrl.href, window.location.href);
            if (!finalUrl.hash && requestedUrl.hash &&
                finalUrl.pathname === requestedUrl.pathname &&
                finalUrl.search === requestedUrl.search) {
                finalUrl.hash = requestedUrl.hash;
            }

            let historyMode = options.historyMode;
            if (historyMode === 'form') {
                historyMode = response.redirected && finalUrl.href !== window.location.href
                    ? 'push'
                    : 'replace';
            }

            if (historyMode === 'push' && finalUrl.href !== window.location.href) {
                window.history.replaceState({
                    ...(window.history.state || {}),
                    scrollX: window.scrollX,
                    scrollY: window.scrollY
                }, '', window.location.href);
                window.history.pushState({ scrollX: 0, scrollY: 0 }, '', finalUrl.href);
            } else if (historyMode === 'replace' ||
                (historyMode === 'none' && finalUrl.href !== window.location.href)) {
                window.history.replaceState(window.history.state || {}, '', finalUrl.href);
            }

            document.dispatchEvent(new Event('dv:page-loaded'));

            if (options.restoreScroll) {
                window.scrollTo(options.restoreScroll.x || 0, options.restoreScroll.y || 0);
            } else if (finalUrl.hash) {
                let anchorId = finalUrl.hash.slice(1);
                try {
                    anchorId = decodeURIComponent(anchorId);
                } catch (error) {
                    console.warn('Não foi possível decodificar a âncora da página.', error);
                }
                const anchor = document.getElementById(anchorId);
                if (anchor) anchor.scrollIntoView();
            } else {
                window.scrollTo(0, 0);
                const main = document.querySelector('main.dv-main');
                if (main) {
                    main.setAttribute('tabindex', '-1');
                    main.focus({ preventScroll: true });
                    main.addEventListener('blur', () => main.removeAttribute('tabindex'), { once: true });
                }
            }

            if (!response.ok) {
                dvToast(`A página respondeu com erro (${response.status}).`, 'error');
            }
        });
    }

    async function requestPage(url, options = {}) {
        const requestId = ++latestPageRequest;
        const method = options.method || 'GET';
        const requestedUrl = new URL(url, window.location.href);
        document.documentElement.classList.add('dv-ajax-navigation-pending');
        const currentMain = document.querySelector('main.dv-main');
        if (currentMain) currentMain.setAttribute('aria-busy', 'true');

        try {
            const response = await fetch(requestedUrl.href, {
                method,
                body: options.body,
                credentials: 'same-origin',
                headers: { Accept: 'text/html' }
            });

            if (requestId !== latestPageRequest) return;
            await renderFetchedPage(response, requestedUrl, options, requestId);
        } catch (error) {
            if (requestId !== latestPageRequest) return;
            console.error('Falha ao carregar a página com AJAX:', error);
            if (method === 'GET' && options.allowFallback !== false) {
                window.location.assign(requestedUrl.href);
            } else {
                dvToast(
                    method === 'GET'
                        ? 'Não foi possível carregar esta página. Tente novamente.'
                        : 'Não foi possível confirmar o envio. Verifique a conexão antes de tentar novamente.',
                    'error',
                    6000
                );
            }
        } finally {
            if (requestId === latestPageRequest) {
                document.documentElement.classList.remove('dv-ajax-navigation-pending');
                const main = document.querySelector('main.dv-main');
                if (main) main.removeAttribute('aria-busy');
            }
        }
    }

    function initializePageInteractions() {
        initReservations();
        initCancelReservations();
        initPresenceAdmin();
        initForum();
        initNotifications();
        initAdminModals();
        initTrailerModal();
        initCatalogFilter();
        initMobileMenu();
        initAjaxNavigation();
    }

    function initAjaxNavigation() {
        addDocumentListener('ajax-navigation-click', 'click', (event) => {
            if (event.defaultPrevented || event.button !== 0 ||
                event.metaKey || event.ctrlKey || event.shiftKey || event.altKey ||
                !(event.target instanceof Element)) {
                return;
            }

            const link = event.target.closest('a[href]');
            if (!link || link.hasAttribute('download') ||
                (link.target && link.target !== '_self') ||
                link.relList.contains('external') ||
                link.hasAttribute('data-no-ajax')) {
                return;
            }

            let targetUrl;
            try {
                targetUrl = new URL(link.href, window.location.href);
            } catch (error) {
                return;
            }

            if (targetUrl.origin !== window.location.origin ||
                !['http:', 'https:'].includes(targetUrl.protocol) ||
                (targetUrl.pathname === window.location.pathname &&
                    targetUrl.search === window.location.search &&
                    targetUrl.hash)) {
                return;
            }

            event.preventDefault();
            const offcanvas = link.closest('.offcanvas');
            if (offcanvas && window.bootstrap) {
                let navigated = false;
                let fallbackTimer;
                const continueNavigation = () => {
                    if (navigated) return;
                    navigated = true;
                    window.clearTimeout(fallbackTimer);
                    requestPage(targetUrl.href, { historyMode: 'push' });
                };

                offcanvas.addEventListener('hidden.bs.offcanvas', continueNavigation, { once: true });
                window.bootstrap.Offcanvas.getOrCreateInstance(offcanvas).hide();
                fallbackTimer = window.setTimeout(continueNavigation, 500);
                return;
            }

            requestPage(targetUrl.href, { historyMode: 'push' });
        });

        addDocumentListener('ajax-form-submit', 'submit', (event) => {
            if (event.defaultPrevented || !(event.target instanceof HTMLFormElement)) return;

            const form = event.target;
            if (form.hasAttribute('data-no-ajax') ||
                (form.target && form.target !== '_self')) {
                return;
            }

            const method = form.method.toUpperCase();
            if (!['GET', 'POST'].includes(method)) return;

            const formData = new FormData(form);
            if (method === 'GET') {
                if (form.querySelector('input[type="file"]')) return;
                const targetUrl = new URL(form.action, window.location.href);
                const params = new URLSearchParams();
                formData.forEach((value, key) => {
                    if (typeof value === 'string') params.append(key, value);
                });
                targetUrl.search = params.toString();
                event.preventDefault();
                requestPage(targetUrl.href, { historyMode: 'push' });
                return;
            }

            const submitter = event.submitter;
            if (submitter && submitter.name && !formData.has(submitter.name)) {
                formData.append(submitter.name, submitter.value);
            }

            event.preventDefault();
            if (submitter instanceof HTMLElement && 'disabled' in submitter) {
                submitter.disabled = true;
            }
            form.setAttribute('aria-busy', 'true');
            requestPage(form.action, { method, body: formData, historyMode: 'form' }).finally(() => {
                if (!form.isConnected) return;
                form.removeAttribute('aria-busy');
                if (submitter instanceof HTMLElement && 'disabled' in submitter) {
                    submitter.disabled = false;
                }
            });
        });
    }

    window.addEventListener('popstate', (event) => {
        requestPage(window.location.href, {
            historyMode: 'none',
            restoreScroll: event.state
                ? { x: event.state.scrollX, y: event.state.scrollY }
                : null
        });
    });

    if (!window.history.state) {
        window.history.replaceState({ scrollX: window.scrollX, scrollY: window.scrollY }, '', window.location.href);
    }

    document.addEventListener('DOMContentLoaded', initializePageInteractions);
    document.addEventListener('dv:page-loaded', initializePageInteractions);

})();

$(document).ready(function() {
    console.log("Document ready - initializing scripts and custom modal");

    // DOM Elements
    const $sidebar = $('.sidebar');
    const $profileHeader = $('#profileHeader');
    const $sidebarToggleMobile = $('#sidebarToggleMobile');
    const $sidebarToggleDesktop = $('#sidebarToggleDesktop');
    const $mainContent = $('.main-content');
    const $sidebarOverlay = $('#sidebarOverlay');
    const $quickAccessBar = $('.quick-access-bar');
    const $themeToggle = $('.theme-toggle');
    const $body = $('html');

    // State Variables
    let isSidebarOpen = false;
    let isDropdownOpen = false;
    let lastScroll = 0;
    let deferredPrompt = null;

    // Notification Banner
    const $notificationBanner = $('#notificationBanner');

    function showNotification(message, type = 'info') {
        const alertClass = {
            'success': 'alert-success',
            'error': 'alert-error',
            'info': 'alert-info'
        }[type] || 'alert-info';
        const content = `<div class="alert-custom ${alertClass}"><i class="fas fa-check-circle"></i> ${message}</div>`;
        $notificationBanner.html(content).css('display', 'block').animate({ top: '0' }, 300);

        setTimeout(() => {
            $notificationBanner.animate({ top: '-100%' }, 300, () => {
                $notificationBanner.css('display', 'none').css('top', '-100px');
            });
        }, 3000);
    }

    // Custom Modal Functions
    const customModal = document.getElementById('customModal');
    const customModalTitle = document.getElementById('customModalTitle');
    const customModalBody = document.getElementById('customModalBody');
    const customModalClose = document.getElementById('customModalClose');

    function showCustomModal(title, content, onClose = null) {
        if (customModal && customModalTitle && customModalBody) {
            customModalTitle.textContent = title;
            customModalBody.innerHTML = content;
            customModal.style.display = 'flex';

            customModalClose.onclick = function() {
                customModal.style.display = 'none';
                if (onClose) onClose();
            };

            // Close on backdrop click
            customModal.onclick = function(e) {
                if (e.target === customModal) {
                    customModal.style.display = 'none';
                    if (onClose) onClose();
                }
            };

            // Close on Esc key
            document.addEventListener('keydown', function handleEsc(e) {
                if (e.key === 'Escape') {
                    customModal.style.display = 'none';
                    if (onClose) onClose();
                    document.removeEventListener('keydown', handleEsc);
                }
            });
        }
    }

    // Expose showNotification and showCustomModal to global scope
    window.showNotification = showNotification;
    window.showCustomModal = showCustomModal;

    // Show message modal if messages exist on page load
    if ('{% if messages %}true{% else %}false{% endif %}' === 'true') {
        setTimeout(() => {
            window.showCustomModal('Initial message from server', 'Initial message from server', 'info');
        }, 100);
    }

    // Homescreen Installation Prompt
    window.addEventListener('beforeinstallprompt', (e) => {
        e.preventDefault();
        deferredPrompt = e;
        console.log('Beforeinstallprompt event captured');
        if (isMobile() && !window.matchMedia('(display-mode: standalone)').matches && !localStorage.getItem('installPromptShown')) {
            const content = `
                <p>Install Corps Connect on your device for quick access! Tap the button below and follow the instructions.</p>
                <button id="installButton" class="btn btn-custom w-100 mt-3">Add to Homescreen</button>
            `;
            showCustomModal('Add to Homescreen', content, () => {
                localStorage.setItem('installPromptShown', 'true');
                console.log('Install modal closed');
            });

            $('#installButton').on('click', () => {
                if (deferredPrompt) {
                    console.log('Triggering install prompt');
                    deferredPrompt.prompt();
                    deferredPrompt.userChoice.then((choiceResult) => {
                        if (choiceResult.outcome === 'accepted') {
                            console.log('User accepted the install prompt');
                        } else {
                            console.log('User dismissed the install prompt');
                        }
                        deferredPrompt = null;
                        customModal.style.display = 'none';
                    }).catch(err => {
                        console.error('Error with user choice:', err);
                    });
                } else {
                    console.log('No deferred prompt available');
                }
            });
        }
    });

    $('#addToHomescreenBtn').on('click', () => {
        if (deferredPrompt) {
            console.log('Triggering install prompt from sidebar');
            deferredPrompt.prompt();
            deferredPrompt.userChoice.then((choiceResult) => {
                if (choiceResult.outcome === 'accepted') {
                    console.log('User accepted the install prompt');
                } else {
                    console.log('User dismissed the install prompt');
                }
                deferredPrompt = null;
            }).catch(err => {
                console.error('Error with user choice:', err);
            });
        } else {
            console.log('No deferred prompt available');
            showCustomModal('Error', '<p>Install prompt is not available at this time.</p>');
        }
    });

    // Utility Functions
    function getCookie(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        console.log('CSRF Token:', cookieValue);
        return cookieValue;
    }

    function isMobile() {
        return /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent);
    }

    function updateToggleIcon(theme) {
        const $icon = $themeToggle.find('i');
        console.log("Updating toggle icon for theme:", theme);
        $icon.removeClass('fa-moon fa-sun').addClass(theme === 'dark' ? 'fa-sun' : 'fa-moon');
    }

    function toggleSidebar() {
        if (!isSidebarOpen) {
            $sidebar.addClass('open');
            if (window.innerWidth > 991) $mainContent.addClass('shifted');
            $sidebarOverlay.addClass('active');
            isSidebarOpen = true;
        } else {
            $sidebar.removeClass('open');
            $mainContent.removeClass('shifted');
            $sidebarOverlay.removeClass('active');
            isSidebarOpen = false;
        }
    }

    // Event Handlers
    $sidebarToggleDesktop.on('click', function(e) {
        e.preventDefault();
        toggleSidebar();
    });

    $profileHeader.on('click', function(e) {
        e.preventDefault();
        if (!isDropdownOpen) {
            $(this).dropdown('show');
            isDropdownOpen = true;
        }
    });

    $('.dropdown-menu').on('hidden.bs.dropdown', function() {
        isDropdownOpen = false;
    });

    $sidebarToggleMobile.on('click', function(e) {
        e.preventDefault();
        toggleSidebar();
    });

    $sidebarOverlay.on('click touchstart', function(e) {
        e.preventDefault();
        toggleSidebar();
    });

    $(document).on('click touchstart', function(e) {
        if (!$(e.target).closest('.profile-header').length && !$(e.target).closest('.dropdown-menu').length && isDropdownOpen) {
            $('.dropdown-menu').dropdown('hide');
            isDropdownOpen = false;
        }
        if (!$(e.target).closest('.sidebar').length && !$(e.target).closest('#sidebarToggleMobile').length && !$(e.target).closest('#sidebarToggleDesktop').length && isSidebarOpen) {
            toggleSidebar();
        }
    });

    // Enhanced Dropdown Handling
    $(document).on('show.bs.dropdown', '.dropdown', function(e) {
        const $dropdownMenu = $(this).find('.dropdown-menu');
        $dropdownMenu.css('z-index', 1106); // Ensure highest z-index
        $dropdownMenu.addClass('show');
        $(this).closest('.sidebar-header, .list-group-item').css('position', 'relative').css('z-index', 1105); // Elevate parent
    });

    $(document).on('hidden.bs.dropdown', '.dropdown', function(e) {
        const $dropdownMenu = $(this).find('.dropdown-menu');
        $dropdownMenu.removeClass('show');
        $(this).closest('.sidebar-header, .list-group-item').css('z-index', ''); // Reset parent z-index
    });

    $(window).on('scroll', function() {
        const currentScroll = $(this).scrollTop();
        if (currentScroll > lastScroll && currentScroll > 100) {
            $quickAccessBar.addClass('hidden');
        } else {
            $quickAccessBar.removeClass('hidden');
        }
        lastScroll = currentScroll;
    });

    $(document).on('click', '.dropdown-toggle', function(e) {
        console.log("Dropdown clicked for:", $(this).attr('id'));
    });

    $('#notificationQuickAccess').on('click', function(e) {
        if ('{{ user.is_authenticated }}' === 'True') {
            const csrfToken = getCookie('csrftoken');
            if (csrfToken) {
                $.ajax({
                    url: '{% url "mark_notifications_read" %}',
                    method: 'POST',
                    headers: { 'X-CSRFToken': csrfToken, 'X-Requested-With': 'XMLHttpRequest' },
                    success: function(data) {
                        console.log('Mark read response:', data);
                        if (data.status === 'success') {
                            $('#notificationQuickAccess .badge').remove();
                            checkNotifications();
                        } else {
                            console.log('Failed to mark notifications as read:', data.message);
                        }
                    },
                    error: function(xhr) {
                        console.log('Error marking notifications as read:', xhr.status, xhr.responseText);
                    }
                });
            }
        }
    });

    // Theme Toggle
    const currentTheme = localStorage.getItem('theme') || 'dark';
    $body.attr('data-theme', currentTheme);
    console.log("Initial theme set to:", currentTheme);
    updateToggleIcon(currentTheme);

    $themeToggle.on('click', function() {
        console.log("Theme toggle clicked");
        const newTheme = $body.attr('data-theme') === 'dark' ? 'light' : 'dark';
        $body.attr('data-theme', newTheme);
        localStorage.setItem('theme', newTheme);
        console.log("Theme switched to:", newTheme);
        updateToggleIcon(newTheme);
    });

    // Notification Polling
    function checkNotifications() {
        if ('{{ user.is_authenticated }}' === 'True') {
            console.log('Checking notifications...');
            $.get('{% url "check_notifications" %}', function(data) {
                console.log('Notification check response:', data);
                const unreadCount = data.unread_count;
                const $bell = $('#notificationQuickAccess');
                const $badge = $bell.find('.badge');
                if (unreadCount > 0) {
                    if ($badge.length) {
                        $badge.text(unreadCount);
                    } else {
                        $bell.append(`<span class="badge rounded-circle bg-danger position-absolute" style="top: -5px; right: -5px; width: 1rem; height: 1rem; font-size: 0.75rem; display: flex; align-items: center; justify-content: center;">${unreadCount}<span class="visually-hidden">unread notifications</span></span>`);
                    }
                } else {
                    $badge.remove();
                }
            }).fail(function(xhr) {
                console.log('Failed to fetch notifications:', xhr.status, xhr.responseText);
            });
        }
    }

    setInterval(checkNotifications, 60000);
    checkNotifications();

    // Resize Handler
    $(window).on('resize', function() {
        if (window.innerWidth > 991) {
            $sidebar.removeClass('open');
            $mainContent.removeClass('shifted');
            $sidebarOverlay.removeClass('active');
            isSidebarOpen = false;
        }
    }).trigger('resize');

    // Service Worker Registration
    if ('serviceWorker' in navigator) {
        navigator.serviceWorker.register('/static/nysc/js/service-worker.js')
            .then(() => console.log('Service Worker registered'))
            .catch((error) => console.error('Service Worker registration failed:', error));
    }

    // Marketplace Email Subscription AJAX
    $('#emailSubscriptionForm').on('submit', function(e) {
        console.log("Form submit triggered for email subscription");
        e.preventDefault();
        const email = $('#subscriptionEmail').val();
        const csrfToken = getCookie('csrftoken');
        if (!csrfToken) {
            console.error('CSRF token not found');
            showCustomModal('Error', '<p>An error occurred. Please reload the page.</p>');
            return;
        }
        console.log("Sending AJAX to:", '{% url "marketplace_subscribe" %}', "with email:", email, "and CSRF:", csrfToken);
        $.ajax({
            url: '{% url "marketplace_subscribe" %}',
            method: 'POST',
            data: { email: email, csrfmiddlewaretoken: csrfToken },
            success: function(response) {
                console.log("AJAX Success:", response);
                showCustomModal('Success', `<p>${response.message}</p>`, () => {
                    $('#subscriptionEmail').val('');
                });
                setTimeout(() => customModal.style.display = 'none', 3000);
            },
            error: function(xhr) {
                console.error('AJAX Error:', xhr.status, xhr.responseJSON || xhr.responseText);
                const response = xhr.responseJSON || { message: 'An unknown error occurred.' };
                showCustomModal('Error', `<p>${response.message}</p>`);
                setTimeout(() => customModal.style.display = 'none', 3000);
            }
        });
    });

    // Handle PPA deletion
    $(document).on('click', '.delete-ppa', function(e) {
        e.preventDefault();
        const ppaId = $(this).data('ppa-id');
        // Use data-ppa-name attribute for the PPA name instead of .text()
        const ppaName = $(this).closest('.list-group-item').find('a').data('ppa-name') || $(this).closest('.list-group-item').find('a').text().trim();

        const content = `
            <p>Are you sure you want to delete the PPA "${ppaName}"? This action cannot be undone.</p>
            <div class="d-flex gap-2 mt-3">
                <button id="confirmDeleteBtn" class="btn btn-danger" data-ppa-id="${ppaId}">Yes, Delete</button>
                <button id="cancelDeleteBtn" class="btn btn-secondary">Cancel</button>
            </div>
        `;
        showCustomModal('Confirm Delete', content, () => {
            // Reset on close if not confirmed
        });

        $('#confirmDeleteBtn').on('click', function() {
            const csrfToken = getCookie('csrftoken');
            if (!csrfToken) {
                console.error('CSRF token not found');
                showCustomModal('Error', '<p>An error occurred. Please reload the page.</p>');
                return;
            }

            $.ajax({
                url: `/ppa/${ppaId}/delete/`,
                method: 'POST',
                headers: {
                    'X-CSRFToken': csrfToken
                },
                data: {},
                beforeSend: function() {
                    $('#confirmDeleteBtn').prop('disabled', true).text('Deleting...');
                },
                success: function(response) {
                    console.log('AJAX success for delete:', response);
                    if (response.status === 'success') {
                        $(`.list-group-item:contains("${ppaName}")`).remove();
                        showNotification(`PPA "${ppaName}" deleted successfully!`, 'success');
                        customModal.style.display = 'none';
                        // Optionally reload the page or update the PPA count
                        // location.reload(); // or update UI dynamically
                    } else {
                        showCustomModal('Error', `<p>${response.message || 'An error occurred.'}</p>`);
                    }
                },
                error: function(xhr) {
                    console.log('AJAX error for delete:', xhr.status, xhr.responseText);
                    showCustomModal('Error', '<p>Failed to delete PPA. Please try again.</p>');
                },
                complete: function() {
                    $('#confirmDeleteBtn').prop('disabled', false).text('Yes, Delete');
                }
            });
        });

        $('#cancelDeleteBtn').on('click', function() {
            customModal.style.display = 'none';
        });
    });

    // Marketplace Feedback Submission AJAX
    $('#feedbackForm').on('submit', function(e) {
        console.log("Form submit triggered for feedback");
        e.preventDefault();
        const feedback = $('#feedbackText').val();
        const csrfToken = getCookie('csrftoken');
        if (!csrfToken) {
            console.error('CSRF token not found');
            showCustomModal('Error', '<p>An error occurred. Please reload the page.</p>');
            return;
        }
        console.log("Sending AJAX to:", '{% url "marketplace_feedback" %}', "with feedback:", feedback, "and CSRF:", csrfToken);
        $.ajax({
            url: '{% url "marketplace_feedback" %}',
            method: 'POST',
            data: { feedback: feedback, csrfmiddlewaretoken: csrfToken },
            success: function(response) {
                console.log("AJAX Success:", response);
                showCustomModal('Success', `<p>${response.message}</p>`, () => {
                    $('#feedbackText').val('');
                });
                setTimeout(() => customModal.style.display = 'none', 3000);
            },
            error: function(xhr) {
                console.error('AJAX Error:', xhr.status, xhr.responseJSON || xhr.responseText);
                const response = xhr.responseJSON || { message: 'An unknown error occurred.' };
                showCustomModal('Error', `<p>${response.message}</p>`);
                setTimeout(() => customModal.style.display = 'none', 3000);
            }
        });
    });

    // Follow/Unfollow AJAX
    $(document).on('click', '.follow-btn, #follow-btn', function(e) {
        e.preventDefault();
        console.log('Follow button clicked', $(this).data('user') || $(this).data('username'));
        const $button = $(this);
        let username, isFollowing;

        if ($button.is('#follow-btn')) {
            username = $button.data('username');
            isFollowing = $button.data('action') === 'unfollow';
        } else {
            username = $button.data('user');
            isFollowing = $button.data('following') === 'true';
        }

        if (!username) {
            console.error('Username data attribute missing');
            return;
        }

        const baseFollowUrl = '/profile/';
        const baseUnfollowUrl = '/profile/';
        const url = isFollowing ? `${baseUnfollowUrl}${encodeURIComponent(username)}/unfollow/` : `${baseFollowUrl}${encodeURIComponent(username)}/follow/`;

        console.log('Sending request to:', url);

        $.ajax({
            url: url,
            method: 'POST',
            headers: {
                'X-CSRFToken': getCookie('csrftoken')
            },
            data: {},
            beforeSend: function() {
                $button.prop('disabled', true);
                if ($button.is('#follow-btn')) {
                    $button.html('<i class="fas fa-spinner fa-spin"></i> Processing...');
                }
            },
            success: function(response) {
                console.log('AJAX success:', response);
                if (response.status === 'success') {
                    if ($button.is('#follow-btn')) {
                        if (response.action === 'followed') {
                            $button.removeClass('btn-primary').addClass('btn-outline-danger')
                                .html('<i class="fas fa-user-minus"></i> Unfollow')
                                .data('action', 'unfollow');
                        } else {
                            $button.removeClass('btn-outline-danger').addClass('btn-primary')
                                .html('<i class="fas fa-user-plus"></i> Follow')
                                .data('action', 'follow');
                        }
                        $('#followers-count').text(`${response.followers_count} Follower${response.followers_count !== 1 ? 's' : ''}`);
                    } else {
                        if (response.action === 'followed') {
                            $button.text('Unfollow').data('following', 'true');
                        } else {
                            $button.text('Follow').data('following', 'false');
                        }
                    }
                } else {
                    showCustomModal('Error', `<p>${response.message || 'An error occurred.'}</p>`);
                }
            },
            error: function(xhr, status, error) {
                console.log('AJAX error:', status, error, xhr.responseText);
                const errorMsg = xhr.responseJSON ? xhr.responseJSON.message : 'Failed to process request. Check console for details.';
                showCustomModal('Error', `<p>${errorMsg}</p>`);
            },
            complete: function() {
                $button.prop('disabled', false);
                if ($button.is('#follow-btn')) {
                    $button.html($button.data('action') === 'unfollow' ? '<i class="fas fa-user-minus"></i> Unfollow' : '<i class="fas fa-user-plus"></i> Follow');
                }
            }
        });
    });

    // Initialize all Bootstrap modals
    $('.modal').on('shown.bs.modal', function (e) {
        const ppaId = $(this).attr('id').split('_')[1];
        console.log('Modal shown for PPA', ppaId);
        // Ensure form elements are only disabled when intended
        if ($(`#verifyForm_${ppaId} input`).is(':disabled')) {
            console.log('Form elements disabled for PPA', ppaId);
        }
        $(this).find('button.btn-close').on('click', function() {
            $(this).closest('.modal').modal('hide');
        });
    }).on('hidden.bs.modal', function() {
        $(this).find('input, button').prop('disabled', false); // Reset on hide
    });

    // Handle PPA verification request (Updated for dynamic UI update across templates)
    $('form[id^="verifyForm_"]').on('submit', function(e) {
        e.preventDefault();
        console.log('PPA verification form submitted');
        const form = $(this);
        const ppaId = form.attr('id').split('_')[1];
        const formData = new FormData(form[0]);

        $.ajax({
            url: `/ppa/${ppaId}/verify/`,
            type: 'POST',
            headers: {
                'X-CSRFToken': getCookie('csrftoken')
            },
            data: formData,
            processData: false,
            contentType: false,
            beforeSend: function() {
                form.find('button').prop('disabled', true).html('<i class="fas fa-spinner fa-spin"></i> Submitting...');
            },
            success: function(response) {
                console.log('AJAX success for verification:', response);
                if (response.status === 'success') {
                    window.showCustomModal('Success', `<p>${response.message}</p>`, () => {
                        $(`#verifyPPA_${ppaId}`).modal('hide');
                        // Update the verified icon dynamically
                        const $ppaContainer = $(`#verifyPPA_${ppaId}`).closest('.card, .list-group-item');
                        const $verifiedIcon = $ppaContainer.find('.verified-icon');
                        if (response.verified) {
                            if ($verifiedIcon.length) {
                                $verifiedIcon.show(); // Ensure it's visible
                            } else {
                                $ppaContainer.find('.card-title, a').first().append(
                                    '<i class="fas fa-check-circle text-primary verified-icon" data-bs-toggle="tooltip" data-bs-custom-class="custom-tooltip" title="This PPA is verified"></i>'
                                );
                            }
                            // Reinitialize tooltips globally
                            $('[data-bs-toggle="tooltip"]').tooltip('dispose').each(function() {
                                new bootstrap.Tooltip(this, { customClass: 'custom-tooltip', trigger: 'click' });
                            });
                        } else {
                            $verifiedIcon.hide();
                        }
                        // Update dropdown if present
                        const $dropdown = $ppaContainer.find('.dropdown-menu');
                        if ($dropdown.length) {
                            $dropdown.find(`[data-bs-target="#verifyPPA_${ppaId}"]`).text(
                                response.verification_status === 'approved' ? 'Verified' : 'Pending'
                            ).toggleClass('disabled text-success', response.verification_status === 'approved');
                        }
                    });
                } else {
                    window.showCustomModal('Error', `<p>${response.message}</p>`);
                }
            },
            error: function(xhr) {
                console.log('AJAX error for verification:', xhr.status, xhr.responseText);
                window.showCustomModal('Error', '<p>An error occurred. Please try again.</p>');
            },
            complete: function() {
                form.find('button').prop('disabled', false).html('Submit for Verification');
            }
        });
    });

    // Disable form elements for pending status
    $('.pending-btn').on('click', function() {
        const ppaId = $(this).data('bs-target').split('_')[1];
        const form = $(`#verifyForm_${ppaId}`);
        if ($(this).is(':disabled')) {
            showCustomModal('Notice', '<p>Verification is in progress. Please wait for admin review.</p>');
        }
    });

    // Show More Button for Leaderboard
    let visibleRows = 10;
    const totalRows = $('.leaderboard-row').length;
    const maxLimit = 30;

    $('#showMoreBtn').on('click', function(e) {
        e.preventDefault();
        visibleRows += 10;
        if (visibleRows > maxLimit) visibleRows = maxLimit;
        $('.leaderboard-row').each(function(index) {
            if (index < visibleRows) {
                $(this).show();
            }
        });
        if (visibleRows >= totalRows || visibleRows >= maxLimit) {
            $(this).hide();
        }
    });

    // Initial check for follow buttons
    console.log('Follow buttons found:', $('.follow-btn, #follow-btn').length);
});
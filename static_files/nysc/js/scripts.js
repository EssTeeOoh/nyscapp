/*!
* Start Bootstrap - Shop Homepage v5.0.6 (https://startbootstrap.com/template/shop-homepage)
* Copyright 2013-2023 Start Bootstrap
* Licensed under MIT (https://github.com/StartBootstrap/startbootstrap-shop-homepage/blob/master/LICENSE)
*/
// This file is intentionally blank
// Use this file to add JavaScript to your project

$(document).ready(function() {
    console.log("Document ready - initializing scripts");

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

    // Show message modal if messages exist
    if ('{% if messages %}true{% else %}false{% endif %}' === 'true') {
        $('#messageModal').modal('show');
    }

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

    $(document).on('shown.bs.dropdown', '#notificationQuickAccess', function() {
        console.log('Dropdown shown for:', $(this).attr('id'));
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
                        $bell.append(`<span class="badge rounded-pill bg-danger" style="position: absolute; top: -5px; right: -5px; font-size: 0.6em;">${unreadCount}<span class="visually-hidden">unread notifications</span></span>`);
                    }
                } else {
                    $badge.remove();
                }
            }).fail(function(xhr) {
                console.log('Failed to fetch notifications:', xhr.status, xhr.responseText);
            });
        }
    }

    $(document).on('click', '#clearAllNotificationsQuick', function(e) {
        e.preventDefault();
        console.log('Clear notifications clicked');
        if (confirm('Are you sure you want to clear all notifications?')) {
            const csrfToken = getCookie('csrftoken');
            if (csrfToken) {
                $.ajax({
                    url: '{% url "clear_notifications" %}',
                    method: 'POST',
                    headers: { 'X-CSRFToken': csrfToken, 'X-Requested-With': 'XMLHttpRequest' },
                    success: function(data) {
                        console.log('Clear response:', data);
                        if (data.status === 'success') {
                            $('#notificationQuickAccess .badge').remove();
                            $('#notificationQuickAccess + .dropdown-menu').html('<li><a class="dropdown-item text-center text-muted">No notifications</a></li>');
                            alert('All notifications cleared.');
                        } else {
                            alert('Failed to clear notifications.');
                        }
                    },
                    error: function() {
                        alert('An error occurred while clearing notifications.');
                    }
                });
            } else {
                alert('CSRF token not found. Please reload the page.');
            }
        }
    });

    // Poll every 60 seconds
    setInterval(checkNotifications, 60000);
    checkNotifications(); // Initial check

    // Resize Handler
    $(window).on('resize', function() {
        if (window.innerWidth > 991) {
            $sidebar.removeClass('open');
            $mainContent.removeClass('shifted');
            $sidebarOverlay.removeClass('active');
            isSidebarOpen = false;
        }
    }).trigger('resize');

    // Homescreen Installation Prompt
    window.addEventListener('beforeinstallprompt', (e) => {
        e.preventDefault();
        deferredPrompt = e;
        if (isMobile() && !window.matchMedia('(display-mode: standalone)').matches && !localStorage.getItem('installPromptShown')) {
            $('#installModal').modal('show');
            localStorage.setItem('installPromptShown', 'true');
        }
    });

    $('#installButton, #addToHomescreenBtn').on('click', () => {
        if (deferredPrompt) {
            deferredPrompt.prompt();
            deferredPrompt.userChoice.then((choiceResult) => {
                if (choiceResult.outcome === 'accepted') {
                    console.log('User accepted the install prompt');
                } else {
                    console.log('User dismissed the install prompt');
                }
                deferredPrompt = null;
                $('#installModal').modal('hide');
            });
        }
    });

    // Service Worker Registration
    if ('serviceWorker' in navigator) {
        navigator.serviceWorker.register('{% static "nysc/js/service-worker.js" %}')
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
            $('#subscriptionMessage').text('An error occurred. Please reload the page.').addClass('text-danger');
            return;
        }
        console.log("Sending AJAX to:", '{% url "marketplace_subscribe" %}', "with email:", email, "and CSRF:", csrfToken);
        $.ajax({
            url: '{% url "marketplace_subscribe" %}',
            method: 'POST',
            data: { email: email, csrfmiddlewaretoken: csrfToken },
            success: function(response) {
                console.log("AJAX Success:", response);
                $('#subscriptionMessage').text(response.message).removeClass('text-danger').addClass('text-success');
                $('#subscriptionEmail').val('');
                setTimeout(() => $('#subscriptionMessage').text(''), 5000);
            },
            error: function(xhr) {
                console.error('AJAX Error:', xhr.status, xhr.responseJSON || xhr.responseText);
                const response = xhr.responseJSON || { message: 'An unknown error occurred.' };
                $('#subscriptionMessage').text(response.message).removeClass('text-success').addClass('text-danger');
                setTimeout(() => $('#subscriptionMessage').text(''), 5000);
            }
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
            $('#feedbackMessage').text('An error occurred. Please reload the page.').addClass('text-danger');
            return;
        }
        console.log("Sending AJAX to:", '{% url "marketplace_feedback" %}', "with feedback:", feedback, "and CSRF:", csrfToken);
        $.ajax({
            url: '{% url "marketplace_feedback" %}',
            method: 'POST',
            data: { feedback: feedback, csrfmiddlewaretoken: csrfToken },
            success: function(response) {
                console.log("AJAX Success:", response);
                $('#feedbackMessage').text(response.message).removeClass('text-danger').addClass('text-success');
                $('#feedbackText').val('');
                setTimeout(() => $('#feedbackMessage').text(''), 5000);
            },
            error: function(xhr) {
                console.error('AJAX Error:', xhr.status, xhr.responseJSON || xhr.responseText);
                const response = xhr.responseJSON || { message: 'An unknown error occurred.' };
                $('#feedbackMessage').text(response.message).removeClass('text-success').addClass('text-danger');
                setTimeout(() => $('#feedbackMessage').text(''), 5000);
            }
        });
    });
});
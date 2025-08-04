document.addEventListener('DOMContentLoaded', function() {
    const stateSelect = document.getElementById('id_state');
    const lgaSelect = document.getElementById('id_lga');
    const lgaLoading = document.getElementById('lga-loading');
    const form = document.querySelector('form');
    const submitButton = document.getElementById('submitPpaButton');
    const nameInput = document.getElementById('id_name');
    const addressInput = document.getElementById('id_address');

    // Check for required elements (submitButton is optional for LGA functionality)
    if (!stateSelect || !lgaSelect || !lgaLoading || !form || !nameInput || !addressInput) {
        console.error('Missing elements:', {
            stateSelect: !!stateSelect,
            lgaSelect: !!lgaSelect,
            lgaLoading: !!lgaLoading,
            form: !!form,
            submitButton: !!submitButton,
            nameInput: !!nameInput,
            addressInput: !!addressInput
        });
        return;
    }

    // Function to fetch LGA data dynamically
    function fetchLgaData() {
        return fetch('/static/nysc/json/nigeria_lgas.json')
            .then(response => {
                if (!response.ok) {
                    throw new Error(`HTTP error! status: ${response.status}`);
                }
                return response.json();
            })
            .then(data => {
                console.log('LGA data fetched successfully:', Object.keys(data));
                return data;
            })
            .catch(error => {
                console.error('Error loading LGA data:', error);
                alert('Failed to load LGA data. Please try again or contact support.');
                return {};
            });
    }

    // Function to populate LGAs
    function populateLgas(selectedState, lgaData) {
        lgaSelect.innerHTML = '<option value="">Select LGA</option>';
        lgaLoading.classList.remove('d-none');

        if (selectedState && lgaData[selectedState]) {
            console.log('Populating LGAs for state:', selectedState);
            const lgas = lgaData[selectedState] || [];
            console.log('LGAs:', lgas);
            lgas.sort();
            lgas.forEach(lga => {
                const option = document.createElement('option');
                option.value = lga;
                option.textContent = lga;
                lgaSelect.appendChild(option);
            });
            const preSelectedLga = lgaSelect.getAttribute('data-initial-lga');
            if (preSelectedLga && lgas.includes(preSelectedLga)) {
                lgaSelect.value = preSelectedLga;
                console.log('Pre-selected LGA:', preSelectedLga);
            }
        } else {
            console.log('No LGAs for state or invalid state:', selectedState);
        }

        lgaLoading.classList.add('d-none');
    }

    // Initialize and populate LGAs
    fetchLgaData().then(lgaData => {
        const initialState = stateSelect.value;
        if (initialState) {
            console.log('Initializing with state:', initialState);
            populateLgas(initialState, lgaData);
        }

        stateSelect.addEventListener('change', function() {
            const selectedState = this.value;
            console.log('State changed to:', selectedState);
            populateLgas(selectedState, lgaData);
        });

        // Handle form submission with AJAX and duplication check
        if (form && (submitButton || document.querySelector('button[type="submit"]'))) {
            const button = submitButton || document.querySelector('button[type="submit"]');
            form.addEventListener('submit', function(event) {
                event.preventDefault();

                // Disable button immediately to prevent multiple clicks
                button.disabled = true;
                button.innerHTML = `
                    <span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span>
                    Submitting...
                `;

                const selectedState = stateSelect.value;
                const selectedLga = lgaSelect.value;
                const ppaName = nameInput.value.trim();
                const ppaAddress = addressInput.value.trim();

                console.log('Validating form:', { state: selectedState, lga: selectedLga, name: ppaName, address: ppaAddress });

                if (selectedState && !selectedLga) {
                    console.warn('No LGA selected for state:', selectedState);
                    alert('Please select an LGA for the chosen state.');
                    button.disabled = false;
                    button.innerHTML = button.getAttribute('data-original-html') || 'Submit PPA';
                    lgaSelect.focus();
                    return;
                }

                if (selectedState && selectedLga && selectedLga !== '') {
                    const validLgas = lgaData[selectedState] || [];
                    if (!validLgas.includes(selectedLga)) {
                        console.error('Invalid LGA selected:', selectedLga);
                        alert(`"${selectedLga}" is not a valid LGA for ${selectedState}. Please select a valid LGA.`);
                        button.disabled = false;
                        button.innerHTML = button.getAttribute('data-original-html') || 'Submit PPA';
                        lgaSelect.focus();
                        return;
                    }
                } else if (!selectedState && selectedLga) {
                    console.warn('State not selected but LGA is:', selectedLga);
                    alert('Please select a state before choosing an LGA.');
                    button.disabled = false;
                    button.innerHTML = button.getAttribute('data-original-html') || 'Submit PPA';
                    stateSelect.focus();
                    return;
                }

                if (!ppaName || !ppaAddress) {
                    alert('PPA name and address are required.');
                    button.disabled = false;
                    button.innerHTML = button.getAttribute('data-original-html') || 'Submit PPA';
                    return;
                }

                // Store original button HTML to restore later
                if (!button.getAttribute('data-original-html')) {
                    button.setAttribute('data-original-html', button.innerHTML);
                }

                // Check for duplicates before submission
                fetch(`/check-duplicate-ppa/?name=${encodeURIComponent(ppaName)}&address=${encodeURIComponent(ppaAddress)}&state=${encodeURIComponent(selectedState)}&lga=${encodeURIComponent(selectedLga)}`, {
                    method: 'GET',
                    headers: {
                        'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value,
                        'X-Requested-With': 'XMLHttpRequest'
                    }
                })
                .then(response => {
                    if (!response.ok) {
                        throw new Error(`HTTP error! status: ${response.status}`);
                    }
                    return response.json();
                })
                .then(data => {
                    if (data.is_duplicate) {
                        alert(`A PPA with the name "${ppaName}" and address "${ppaAddress}" already exists. Please provide a unique PPA.`);
                        button.disabled = false;
                        button.innerHTML = button.getAttribute('data-original-html') || 'Submit PPA';
                        return;
                    }
                    // Proceed with submission if not duplicate
                    const formData = new FormData(form);

                    fetch(window.location.href, {
                        method: 'POST',
                        body: formData,
                        headers: {
                            'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value,
                            'X-Requested-With': 'XMLHttpRequest'
                        }
                    })
                    .then(response => {
                        if (!response.ok) {
                            throw new Error(`HTTP error! status: ${response.status}`);
                        }
                        return response.json();
                    })
                    .then(data => {
                        console.log('Server response:', data);
                        if (data.success) {
                            window.location.href = data.redirect_url || '/';
                        } else {
                            alert(data.message || 'Submission failed. Please check the form.');
                            if (data.errors) {
                                console.log('Form errors:', data.errors);
                                for (const [field, error] of Object.entries(data.errors)) {
                                    const input = form.querySelector(`#id_${field}`);
                                    if (input) {
                                        const feedback = document.createElement('div');
                                        feedback.className = 'invalid-feedback d-block';
                                        feedback.textContent = error;
                                        const existingFeedback = input.parentElement.querySelector('.invalid-feedback');
                                        if (existingFeedback) existingFeedback.remove();
                                        input.parentElement.appendChild(feedback);
                                        input.classList.add('is-invalid');
                                    }
                                }
                            }
                            button.disabled = false;
                            button.innerHTML = button.getAttribute('data-original-html') || 'Submit PPA';
                        }
                    })
                    .catch(error => {
                        console.error('Submission error:', error);
                        alert('An error occurred. Please try again.');
                        button.disabled = false;
                        button.innerHTML = button.getAttribute('data-original-html') || 'Submit PPA';
                    });
                })
                .catch(error => {
                    console.error('Duplicate check error:', error);
                    alert('An error occurred while checking for duplicates. Please try again.');
                    button.disabled = false;
                    button.innerHTML = button.getAttribute('data-original-html') || 'Submit PPA';
                });
            });
        }
    });
});
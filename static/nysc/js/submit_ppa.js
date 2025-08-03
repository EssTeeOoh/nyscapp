document.addEventListener('DOMContentLoaded', function() {
    const stateSelect = document.getElementById('id_state');
    const lgaSelect = document.getElementById('id_lga');
    const lgaLoading = document.getElementById('lga-loading');
    const form = document.querySelector('form');
    const submitButton = document.getElementById('submitPpaButton');

    if (!stateSelect || !lgaSelect || !lgaLoading || !form || !submitButton) {
        console.error('Missing elements:', {
            stateSelect: !!stateSelect,
            lgaSelect: !!lgaSelect,
            lgaLoading: !!lgaLoading,
            form: !!form,
            submitButton: !!submitButton
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
            // Set pre-selected LGA if it exists
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
        // Populate LGAs on page load with initial state
        const initialState = stateSelect.value;
        if (initialState) {
            console.log('Initializing with state:', initialState);
            populateLgas(initialState, lgaData);
        }

        // Populate LGAs on state change
        stateSelect.addEventListener('change', function() {
            const selectedState = this.value;
            console.log('State changed to:', selectedState);
            populateLgas(selectedState, lgaData);
        });

        // Handle form submission with AJAX
        form.addEventListener('submit', function(event) {
            event.preventDefault(); // Prevent default form submission

            const selectedState = stateSelect.value;
            const selectedLga = lgaSelect.value;

            console.log('Validating form:', { state: selectedState, lga: selectedLga });

            if (selectedState && !selectedLga) {
                console.warn('No LGA selected for state:', selectedState);
                alert('Please select an LGA for the chosen state.');
                lgaSelect.focus();
                return;
            }

            if (selectedState && selectedLga && selectedLga !== '') {
                const validLgas = lgaData[selectedState] || [];
                if (!validLgas.includes(selectedLga)) {
                    console.error('Invalid LGA selected:', selectedLga);
                    alert(`"${selectedLga}" is not a valid LGA for ${selectedState}. Please select a valid LGA.`);
                    lgaSelect.focus();
                    return;
                }
            } else if (!selectedState && selectedLga) {
                console.warn('State not selected but LGA is:', selectedLga);
                alert('Please select a state before choosing an LGA.');
                stateSelect.focus();
                return;
            }

            // Disable submit button and show loading icon
            submitButton.disabled = true;
            submitButton.innerHTML = `
                <span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span>
                Submitting...
            `;

            // Collect form data
            const formData = new FormData(form);

            // Send AJAX request
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
                    window.location.href = data.redirect_url || '/'; // Redirect on success
                } else {
                    alert(data.message || 'Submission failed. Please check the form.');
                    if (data.errors) {
                        // Display form errors (optional: update UI with errors)
                        console.log('Form errors:', data.errors);
                        for (const [field, error] of Object.entries(data.errors)) {
                            const input = form.querySelector(`#id_${field}`);
                            if (input) {
                                const feedback = document.createElement('div');
                                feedback.className = 'invalid-feedback d-block';
                                feedback.textContent = error;
                                input.parentElement.appendChild(feedback);
                                input.classList.add('is-invalid');
                            }
                        }
                    }
                    // Re-enable button on failure
                    submitButton.disabled = false;
                    submitButton.innerHTML = 'Submit PPA';
                }
            })
            .catch(error => {
                console.error('Submission error:', error);
                alert('An error occurred. Please try again.');
                // Re-enable button on error
                submitButton.disabled = false;
                submitButton.innerHTML = 'Submit PPA';
            });
        });
    });
});
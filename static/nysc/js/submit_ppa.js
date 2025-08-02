document.addEventListener('DOMContentLoaded', function() {
    const stateSelect = document.getElementById('id_state');
    const lgaSelect = document.getElementById('id_lga');
    const lgaLoading = document.getElementById('lga-loading');
    const form = document.querySelector('form');

    if (!stateSelect || !lgaSelect || !lgaLoading || !form) {
        console.error('Missing elements:', {
            stateSelect: !!stateSelect,
            lgaSelect: !!lgaSelect,
            lgaLoading: !!lgaLoading,
            form: !!form
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

        // Frontend validation on form submission
        form.addEventListener('submit', function(event) {
            const selectedState = stateSelect.value;
            const selectedLga = lgaSelect.value;

            console.log('Validating form:', { state: selectedState, lga: selectedLga });

            if (selectedState && !selectedLga) {
                console.warn('No LGA selected for state:', selectedState);
                alert('Please select an LGA for the chosen state.');
                event.preventDefault();
                lgaSelect.focus();
                return;
            }

            if (selectedState && selectedLga && selectedLga !== '') {
                const validLgas = lgaData[selectedState] || [];
                if (!validLgas.includes(selectedLga)) {
                    console.error('Invalid LGA selected:', selectedLga);
                    alert(`"${selectedLga}" is not a valid LGA for ${selectedState}. Please select a valid LGA.`);
                    event.preventDefault();
                    lgaSelect.focus();
                }
            } else if (!selectedState && selectedLga) {
                console.warn('State not selected but LGA is:', selectedLga);
                alert('Please select a state before choosing an LGA.');
                event.preventDefault();
                stateSelect.focus();
            }
        });
    });
});
document.addEventListener('DOMContentLoaded', function() {
    const stateSelect = document.getElementById('id_search_state');
    const lgaSelect = document.getElementById('id_search_lga'); // Matches the form field ID
    const lgaLoading = document.getElementById('lga-loading');

    if (!stateSelect || !lgaSelect || !lgaLoading) {
        console.error('Missing elements:', {
            stateSelect: !!stateSelect,
            lgaSelect: !!lgaSelect,
            lgaLoading: !!lgaLoading
        });
        return;
    }

    // Function to fetch LGA data dynamically from the API endpoint
    function fetchLgaData(selectedState) {
        return fetch(`/api/lgas/?state=${encodeURIComponent(selectedState)}`)
            .then(response => {
                if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
                return response.json();
            })
            .then(data => {
                console.log('LGA data fetched for state:', selectedState, data);
                return data;
            })
            .catch(error => {
                console.error('Error loading LGA data:', error);
                return [];
            });
    }

    // Function to populate LGAs
    function populateLgas(selectedState) {
        lgaSelect.innerHTML = '<option value="">All LGAs</option>';
        lgaLoading.classList.remove('d-none');

        if (selectedState) {
            fetchLgaData(selectedState).then(lgas => {
                lgas.forEach(lga => {
                    const option = document.createElement('option');
                    option.value = lga;
                    option.textContent = lga;
                    lgaSelect.appendChild(option);
                });
                lgaLoading.classList.add('d-none');
            });
        } else {
            lgaLoading.classList.add('d-none');
        }
    }

    // Populate LGAs on page load if state is pre-selected
    const initialState = stateSelect.value;
    if (initialState) {
        console.log('Initializing with state:', initialState);
        populateLgas(initialState);
    }

    // Populate LGAs on state change
    stateSelect.addEventListener('change', function() {
        const selectedState = this.value;
        console.log('State changed to:', selectedState);
        populateLgas(selectedState);
    });

    // Re-populate LGAs after form submission (page reload) using URL params
    if (window.history.replaceState) {
        window.addEventListener('load', function() {
            const urlParams = new URLSearchParams(window.location.search);
            const stateParam = urlParams.get('state');
            if (stateParam) {
                console.log('Re-populating LGAs for state from URL:', stateParam);
                stateSelect.value = stateParam; // Set the state select value
                populateLgas(stateParam);
                const lgaParam = urlParams.get('lga');
                if (lgaParam && lgaSelect.querySelector(`option[value="${lgaParam}"]`)) {
                    lgaSelect.value = lgaParam;
                    console.log('Set LGA from URL:', lgaParam);
                }
            }
        });
    }
});
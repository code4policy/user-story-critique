// DOM Elements
const form = document.getElementById('storyForm');
const apiKeyInput = document.getElementById('apiKey');
const userStoryInput = document.getElementById('userStory');
const definitionOfDoneInput = document.getElementById('definitionOfDone');
const submitButton = document.getElementById('submitButton');
const feedbackContainer = document.getElementById('feedbackContainer');
const feedbackContent = document.getElementById('feedbackContent');
const errorAlert = document.getElementById('errorAlert');
const toggleApiKeyBtn = document.getElementById('toggleApiKey');
const rememberKeyCheckbox = document.getElementById('rememberKey');
const spinner = submitButton.querySelector('.spinner-border');

let prompts = []; // Will store prompts loaded from JSON

// Initialize
document.addEventListener('DOMContentLoaded', async () => {
    // Load saved API key if exists
    const savedApiKey = localStorage.getItem('openai_api_key');
    if (savedApiKey) {
        apiKeyInput.value = savedApiKey;
        rememberKeyCheckbox.checked = true;
    }

    // Load prompts from JSON file
    try {
        const response = await fetch('attached_assets/prompts.json');
        if (!response.ok) {
            throw new Error('Failed to load prompts');
        }
        prompts = await response.json();
    } catch (error) {
        showError('Failed to load analysis prompts. Please try again later.');
    }
});

// Toggle API key visibility
toggleApiKeyBtn.addEventListener('click', () => {
    const type = apiKeyInput.type === 'password' ? 'text' : 'password';
    apiKeyInput.type = type;
    toggleApiKeyBtn.textContent = type === 'password' ? 'Show' : 'Hide';
});

// Form submission
form.addEventListener('submit', async (e) => {
    e.preventDefault();

    // Validate form
    if (!form.checkValidity()) {
        e.stopPropagation();
        form.classList.add('was-validated');
        return;
    }

    if (prompts.length === 0) {
        showError('Analysis prompts not loaded. Please refresh the page.');
        return;
    }

    // Remember API key if checkbox is checked
    if (rememberKeyCheckbox.checked) {
        localStorage.setItem('openai_api_key', apiKeyInput.value);
    } else {
        localStorage.removeItem('openai_api_key');
    }

    // Show loading state
    setLoadingState(true);
    hideError();
    feedbackContainer.classList.add('d-none');

    try {
        const feedback = await analyzeuserStory();
        displayFeedback(feedback);
    } catch (error) {
        showError(error.message);
    } finally {
        setLoadingState(false);
    }
});

async function analyzeuserStory() {
    const feedback = [];

    for (const prompt of prompts) {
        const response = await fetch('https://api.openai.com/v1/chat/completions', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${apiKeyInput.value}`
            },
            body: JSON.stringify({
                model: "gpt-3.5-turbo",
                messages: [
                    {
                        role: "system",
                        content: "You are an expert in agile methodologies and user story writing. Provide specific, actionable feedback."
                    },
                    {
                        role: "user",
                        content: `User Story: ${userStoryInput.value}\nDefinition of Done: ${definitionOfDoneInput.value}\n\n${prompt.prompt}`
                    }
                ],
                temperature: 0.7,
                max_tokens: 250
            })
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.error?.message || 'Failed to get feedback');
        }

        const data = await response.json();
        feedback.push({
            title: prompt.title,
            content: data.choices[0].message.content
        });
    }

    return feedback;
}

function displayFeedback(feedback) {
    feedbackContent.innerHTML = '';

    feedback.forEach((item, index) => {
        const accordionItem = document.createElement('div');
        accordionItem.className = 'accordion-item feedback-item';
        accordionItem.style.animationDelay = `${index * 0.1}s`;

        accordionItem.innerHTML = `
            <h2 class="accordion-header">
                <button class="accordion-button ${index !== 0 ? 'collapsed' : ''}" type="button" 
                    data-bs-toggle="collapse" data-bs-target="#collapse${index}">
                    ${item.title}
                </button>
            </h2>
            <div id="collapse${index}" class="accordion-collapse collapse ${index === 0 ? 'show' : ''}"
                data-bs-parent="#feedbackContent">
                <div class="accordion-body">
                    ${item.content.replace(/\n/g, '<br>')}
                </div>
            </div>
        `;

        feedbackContent.appendChild(accordionItem);
    });

    feedbackContainer.classList.remove('d-none');
}

function setLoadingState(isLoading) {
    submitButton.disabled = isLoading;
    spinner.classList.toggle('d-none', !isLoading);
    submitButton.textContent = isLoading ? 'Analyzing...' : 'Get Feedback';
    if (isLoading) {
        submitButton.prepend(spinner);
    }
}

function showError(message) {
    errorAlert.textContent = message;
    errorAlert.classList.remove('d-none');
}

function hideError() {
    errorAlert.classList.add('d-none');
}
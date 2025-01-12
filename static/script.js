// Previous imports and DOM elements remain unchanged

async function saveFeedbackToSheet(userStory, definitionOfDone, feedback) {
    try {
        const response = await fetch('/save-feedback', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                userStory,
                definitionOfDone,
                feedback
            })
        });

        const data = await response.json();
        if (!data.success) {
            throw new Error(data.message || 'Failed to save feedback');
        }
    } catch (error) {
        console.error('Error saving feedback:', error);
        showError('Failed to save feedback to Google Sheets. Your feedback was still generated successfully.');
    }
}

// Modify the form submission handler to save feedback
form.addEventListener('submit', async (e) => {
    e.preventDefault();

    // Previous validation code remains unchanged

    // Show loading state
    setLoadingState(true);
    hideError();
    feedbackContainer.classList.add('d-none');

    try {
        const feedback = await analyzeuserStory();
        displayFeedback(feedback);
        
        // Save feedback to Google Sheets
        await saveFeedbackToSheet(
            userStoryInput.value,
            definitionOfDoneInput.value,
            feedback
        );
    } catch (error) {
        showError(error.message);
    } finally {
        setLoadingState(false);
    }
});

// Rest of the file remains unchanged

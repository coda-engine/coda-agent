const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export const submitFeedback = async (messageId: string, score: number, comment?: string) => {
    const response = await fetch(`${API_URL}/api/v1/messages/${messageId}/feedback`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ score, comment }),
    });

    if (!response.ok) {
        const text = await response.text();
        throw new Error(`Failed to submit feedback: ${response.status} ${response.statusText} - ${text}`);
    }

    return response.json();
};

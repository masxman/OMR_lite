document.getElementById('search-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const regNo = document.getElementById('reg-input').value.trim();
    if (!regNo) return;
    
    // UI Elements
    const loader = document.getElementById('loader');
    const resultPanel = document.getElementById('result-panel');
    const errorMessage = document.getElementById('error-message');
    const btn = document.getElementById('search-btn');
    
    // Reset State
    resultPanel.classList.add('hidden');
    errorMessage.classList.add('hidden');
    loader.style.display = 'block';
    btn.disabled = true;
    
    try {
        const response = await fetch(`/api/student/${encodeURIComponent(regNo)}`);
        const data = await response.json();
        
        if (response.ok) {
            // Populate Data
            document.getElementById('res-reg').textContent = data.register_number;
            document.getElementById('res-score').textContent = data.total_score;
            document.getElementById('res-rank').textContent = data.rank_range;

            
            // Show Results
            resultPanel.classList.remove('hidden');
            
            // Trigger a small animation
            resultPanel.style.transform = 'translateY(10px)';
            resultPanel.style.opacity = '0';
            setTimeout(() => {
                resultPanel.style.transition = 'all 0.5s cubic-bezier(0.4, 0, 0.2, 1)';
                resultPanel.style.transform = 'translateY(0)';
                resultPanel.style.opacity = '1';
            }, 50);
            
        } else {
            // Show Error
            errorMessage.textContent = `⚠️ ${data.error || 'Registration number not found.'}`;
            errorMessage.classList.remove('hidden');
        }
    } catch (err) {
        errorMessage.textContent = '⚠️ Failed to connect to server. Please try again.';
        errorMessage.classList.remove('hidden');
    } finally {
        loader.style.display = 'none';
        btn.disabled = false;
    }
});

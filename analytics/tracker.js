/**
 * Simple Analytics Tracker
 * Lightweight (<2KB) tracker for page views and clicks
 */

(function() {
    const ANALYTICS_ENDPOINT = 'http://192.168.0.39:5001/api/track';
    
    // Generate or retrieve session ID
    function getSessionId() {
        let sessionId = sessionStorage.getItem('analytics_session_id');
        if (!sessionId) {
            sessionId = 'sess_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
            sessionStorage.setItem('analytics_session_id', sessionId);
        }
        return sessionId;
    }
    
    // Send event to server
    function trackEvent(eventType, data = {}) {
        const payload = {
            session_id: getSessionId(),
            event_type: eventType,
            page: window.location.pathname,
            element: data.element || null,
            metadata: data.metadata || {}
        };
        
        // Use sendBeacon if available (non-blocking), fallback to fetch
        if (navigator.sendBeacon) {
            const blob = new Blob([JSON.stringify(payload)], { type: 'application/json' });
            navigator.sendBeacon(ANALYTICS_ENDPOINT, blob);
        } else {
            fetch(ANALYTICS_ENDPOINT, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload),
                keepalive: true
            }).catch(() => {}); // Silent fail
        }
    }
    
    // Track page view
    function trackPageView() {
        trackEvent('pageview', {
            metadata: {
                referrer: document.referrer,
                title: document.title
            }
        });
    }
    
    // Track clicks on links and buttons
    function setupClickTracking() {
        document.addEventListener('click', function(e) {
            const target = e.target.closest('a, button, [data-track]');
            if (!target) return;
            
            const element = target.getAttribute('data-track') 
                || target.id 
                || target.className 
                || target.tagName.toLowerCase();
            
            const metadata = {
                text: target.textContent.trim().substring(0, 100),
                href: target.href || null
            };
            
            trackEvent('click', { element, metadata });
        }, true);
    }
    
    // Track calculator usage
    function setupCalculatorTracking() {
        // Look for calculator inputs/selects
        const calculatorInputs = document.querySelectorAll(
            '#batteryVoltage, #batteryAh, #motorPower, #avgSpeed, #peakWatts'
        );
        
        if (calculatorInputs.length > 0) {
            let debounceTimer;
            calculatorInputs.forEach(input => {
                input.addEventListener('change', function() {
                    clearTimeout(debounceTimer);
                    debounceTimer = setTimeout(() => {
                        trackEvent('calculator_use', {
                            element: 'range-calculator',
                            metadata: {
                                field: this.id,
                                value: this.value
                            }
                        });
                    }, 1000);
                });
            });
        }
    }
    
    // Initialize tracking when DOM is ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', function() {
            trackPageView();
            setupClickTracking();
            setupCalculatorTracking();
        });
    } else {
        trackPageView();
        setupClickTracking();
        setupCalculatorTracking();
    }
    
    // Track page exit (visibility change)
    let visibilityChangeTracked = false;
    document.addEventListener('visibilitychange', function() {
        if (document.visibilityState === 'hidden' && !visibilityChangeTracked) {
            trackEvent('page_exit', {
                metadata: {
                    timeOnPage: Math.round((Date.now() - performance.timing.navigationStart) / 1000)
                }
            });
            visibilityChangeTracked = true;
        }
    });
    
    console.log('✓ Analytics tracker loaded');
})();

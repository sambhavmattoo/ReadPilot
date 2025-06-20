// Log that the background script has loaded (for debugging)
console.log('Background script loaded');

// Listen for the extension's action button (toolbar icon) being clicked
chrome.action.onClicked.addListener(async (tab) => {
  // Log the action click and intent to open the side panel
  console.log('Action clicked, trying to open side panel');

  try {
    // Attempt to open the side panel for the current tab
    await chrome.sidePanel.open({ tabId: tab.id });
    console.log('Side panel opened successfully');
  } catch (err) {
    // Log if opening the side panel fails (e.g., not supported)
    console.error('Failed to open side panel:', err);
  }

  // If the current tab is a PDF (URL ends with .pdf), inject content.js
  if (tab.url && tab.url.toLowerCase().endsWith('.pdf')) {
    try {
      // Inject content.js into the PDF page to enable PDF detection and messaging
      await chrome.scripting.executeScript({
        target: { tabId: tab.id },
        files: ['content.js'],
      });
      console.log('\u2705 content.js injected into PDF page');
    } catch (err) {
      // Log if script injection fails
      console.error('\u274c Failed to inject content.js:', err);
    }
  }
});

// Listen for messages from content scripts (e.g., PDF detection)
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  // Log all received messages for debugging
  console.log('Background received message:', message);

  // If a PDF was detected, store its URL in Chrome's local storage
  if (message.type === 'PDF_DETECTED' && message.url) {
    chrome.storage.local.set({ currentPDF: message.url }, () => {
      console.log('Stored currentPDF:', message.url);
    });
  }
});

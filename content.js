// Function to determine if the current page is a PDF
function isPDF() {
  // Check if the content type is explicitly PDF
  // Or if the URL ends with .pdf (case-insensitive)
  // Or if there's an <embed> element with type application/pdf
  return document.contentType === 'application/pdf' ||
         window.location.href.toLowerCase().endsWith('.pdf') ||
         document.querySelector('embed[type="application/pdf"]') !== null;
}

// If the current page is a PDF, notify the background script
if (isPDF()) {
  // Log for debugging that a PDF was detected
  console.log('\u2705 isPDF = true, sending message to background.js');
  // Send a message to the background script with the PDF's URL
  chrome.runtime.sendMessage({ type: 'PDF_DETECTED', url: window.location.href }, () => {
    // Callback is empty; could be used for confirmation if needed
  });
}

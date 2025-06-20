// Wait for the DOM to be fully loaded before running any code
// This ensures all elements are available for manipulation

document.addEventListener('DOMContentLoaded', () => {
  // Get references to key UI elements in the side panel
  const sendBtn = document.getElementById('send-btn'); // The send button for chat
  const userInput = document.getElementById('user-input'); // The text input for user queries
  const messagesContainer = document.getElementById('messages'); // The chat message display area
  const container = document.querySelector('.sidepanel-container'); // The main container for styling

  let shifted = false; // Tracks if the UI has shifted after first message
  let currentPDFBlob = null; // Will hold the current PDF as a Blob for upload

  // On load, try to fetch the current PDF from Chrome storage and upload it to Azure
  fetchAndUploadPDF();

  // Handle the send button click for user chat queries
  sendBtn.addEventListener('click', async () => {
    // Get the user's query from the input box
    const query = userInput.value.trim();
    if (!query) return; // Do nothing if input is empty

    // Display the user's message in the chat UI
    appendMessage('You', query, true);
    userInput.value = '';
    sendBtn.disabled = true; // Prevent double sending

    // Shift the UI if this is the first message
    if (!shifted) {
      container.classList.add('shifted');
      shifted = true;
    }

    try {
      // Send the query to the backend API (update the endpoint as needed)
      const response = await fetch('https://your-azure-api-endpoint', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query }),
      });
      // Parse the backend's response (should include answer and references)
      const data = await response.json();
      // Display the AI's answer and any references in the chat UI
      appendMessage('ReadPilot', data.answer, false, data.references);
    } catch (error) {
      // Show an error message if the backend call fails
      appendMessage('ReadPilot', 'Error: Unable to fetch response.', false);
    } finally {
      sendBtn.disabled = false;
      messagesContainer.scrollTop = messagesContainer.scrollHeight;
    }
  });

  /**
   * Appends a chat message to the UI, optionally with references.
   * @param {string} sender - Who sent the message ('You' or 'ReadPilot')
   * @param {string} text - The message text
   * @param {boolean} isUser - True if user, false if AI
   * @param {Array|null} references - Optional array of reference objects
   */
  function appendMessage(sender, text, isUser, references = null) {
    const messageDiv = document.createElement('div');
    messageDiv.classList.add('message');
    messageDiv.classList.add(isUser ? 'user' : 'readpilot');
    messageDiv.innerHTML = `<strong>${sender}:</strong> ${text}`;

    // If the backend provided references, display them below the answer
    if (references && references.length > 0) {
      const refsDiv = document.createElement('div');
      refsDiv.classList.add('references');
      // Build a list of references, each with chapter and page info
      refsDiv.innerHTML = '<em>References:</em><ul style="margin:0;padding-left:18px;">' +
        references.map((ref, idx) => {
          let refText = '';
          if (ref.chapter) refText += `<b>${ref.chapter}</b>`;
          // If both start and end page are present and different, show a range
          if (ref.start_page && ref.end_page && ref.start_page !== ref.end_page) {
            // Make the page range clickable (for future PDF viewer integration)
            refText += ` (<a href="#" onclick="jumpToPage(${ref.start_page});return false;">pages ${ref.start_page}–${ref.end_page}</a>)`;
          } else if (ref.start_page) {
            // Single page reference
            refText += ` (<a href="#" onclick="jumpToPage(${ref.start_page});return false;">page ${ref.start_page}</a>)`;
          }
          return `<li>${refText}</li>`;
        }).join('') +
        '</ul>';
      messageDiv.appendChild(refsDiv);
    }

    messagesContainer.appendChild(messageDiv);
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
  }

  /**
   * Placeholder for PDF page navigation. Integrate with your PDF viewer here.
   * @param {number} pageNum - The page number to jump to
   */
  window.jumpToPage = function(pageNum) {
    // For PDF.js integration, replace this with:
    // if (window.PDFViewerApplication) {
    //   window.PDFViewerApplication.page = pageNum;
    // }
    alert('Jump to page: ' + pageNum + ' (PDF viewer integration needed)');
  };

  /**
   * Fetches the current PDF URL from Chrome storage and uploads it to Azure Blob Storage.
   * This is called on extension load.
   */
  async function fetchAndUploadPDF() {
    try {
      // Get the current PDF URL from Chrome's local storage
      const result = await chrome.storage.local.get(['currentPDF']);
      console.log('currentPDF:', result.currentPDF);

      if (!result.currentPDF) {
        console.log('No currentPDF found in storage.');
        return;
      }

      // Extract the filename from the URL (handles query params)
      const urlParts = result.currentPDF.split('/');
      let filename = urlParts[urlParts.length - 1] || 'document.pdf';
      if (filename.includes('?')) {
        filename = filename.split('?')[0];
      }

      // Download the PDF as a Blob
      const response = await fetch(result.currentPDF);
      if (!response.ok) throw new Error('Failed to fetch PDF from URL');

      currentPDFBlob = await response.blob();

      // Upload the PDF Blob to Azure Blob Storage
      const uploadResponse = await uploadToAzure(currentPDFBlob, filename);
      console.log('PDF uploaded:', uploadResponse);
    } catch (error) {
      console.error('PDF upload failed:', error);
    }
  }

  /**
   * Uploads a Blob to Azure Blob Storage using a SAS URL.
   * @param {Blob} blob - The PDF file as a Blob
   * @param {string} filename - The name to use for the blob
   * @returns {Promise<{success: boolean, url: string}>}
   */
  async function uploadToAzure(blob, filename) {
    // The SAS URL for the Azure Blob Storage container (should be secured in production)
    const containerSasUrl = 'https://readpilotpdfs.blob.core.windows.net/documents?sv=2024-11-04&ss=b&srt=co&sp=rwdlaciytfx&se=2025-06-30T16:14:48Z&st=2025-06-19T08:14:48Z&spr=https&sig=PDUSBLNfbdki9X68ldjb%2FXWHs7avz9Z%2FTKsPEwwwGK8%3D';

    // Split the SAS URL into base and query parts
    const [baseUrl, query] = containerSasUrl.split('?');
    const blobUrl = `${baseUrl}/${filename}?${query}`;

    // Upload the blob using a PUT request
    const response = await fetch(blobUrl, {
      method: 'PUT',
      headers: { 'x-ms-blob-type': 'BlockBlob' },
      body: blob
    });

    if (!response.ok) throw new Error('Azure upload failed');

    return { success: true, url: blobUrl.split('?')[0] };
  }
});

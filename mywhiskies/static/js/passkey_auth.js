function base64urlToBuffer(base64url) {
  const base64 = base64url.replace(/-/g, '+').replace(/_/g, '/');
  const binary = atob(base64);
  const buffer = new ArrayBuffer(binary.length);
  const view = new Uint8Array(buffer);
  for (let i = 0; i < binary.length; i++) view[i] = binary.charCodeAt(i);
  return buffer;
}

function bufferToBase64url(buffer) {
  const bytes = new Uint8Array(buffer);
  let binary = '';
  for (const byte of bytes) binary += String.fromCharCode(byte);
  return btoa(binary).replace(/\+/g, '-').replace(/\//g, '_').replace(/=/g, '');
}

document.getElementById('passkeyLoginBtn').addEventListener('click', async () => {
  const btn = document.getElementById('passkeyLoginBtn');
  const errEl = document.getElementById('passkeyError');
  btn.disabled = true;
  errEl.classList.add('d-none');

  try {
    const beginResp = await fetch('/passkey/authenticate/begin', { method: 'POST' });
    const options = await beginResp.json();

    options.challenge = base64urlToBuffer(options.challenge);
    if (options.allowCredentials) {
      options.allowCredentials = options.allowCredentials.map(c => ({
        ...c, id: base64urlToBuffer(c.id)
      }));
    }

    const credential = await navigator.credentials.get({ publicKey: options });

    const credentialJSON = {
      id: credential.id,
      rawId: bufferToBase64url(credential.rawId),
      response: {
        clientDataJSON: bufferToBase64url(credential.response.clientDataJSON),
        authenticatorData: bufferToBase64url(credential.response.authenticatorData),
        signature: bufferToBase64url(credential.response.signature),
        userHandle: credential.response.userHandle ? bufferToBase64url(credential.response.userHandle) : null,
      },
      type: credential.type,
    };

    const completeResp = await fetch('/passkey/authenticate/complete', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(credentialJSON),
    });

    const result = await completeResp.json();
    if (result.success) {
      window.location.href = result.redirect;
    } else {
      errEl.textContent = result.error || 'Authentication failed. Please try again.';
      errEl.classList.remove('d-none');
      btn.disabled = false;
    }
  } catch (err) {
    if (err.name !== 'NotAllowedError') {
      errEl.textContent = 'Something went wrong. Please try again or use your password.';
      errEl.classList.remove('d-none');
    }
    btn.disabled = false;
  }
});

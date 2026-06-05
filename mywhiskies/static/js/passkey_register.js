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

document.getElementById('addPasskeyBtn').addEventListener('click', async () => {
  const btn = document.getElementById('addPasskeyBtn');
  const errEl = document.getElementById('passkeyRegisterError');
  const nickname = document.getElementById('passkeyNickname')?.value?.trim() || null;
  btn.disabled = true;
  errEl.classList.add('d-none');

  try {
    const beginResp = await fetch('/passkey/register/begin', { method: 'POST' });
    if (!beginResp.ok) throw new Error(`Server error ${beginResp.status} on begin`);
    const options = await beginResp.json();

    options.challenge = base64urlToBuffer(options.challenge);
    options.user.id = base64urlToBuffer(options.user.id);
    if (options.excludeCredentials) {
      options.excludeCredentials = options.excludeCredentials.map(c => ({
        ...c, id: base64urlToBuffer(c.id)
      }));
    }

    const credential = await navigator.credentials.create({ publicKey: options });

    const credentialJSON = {
      id: credential.id,
      rawId: bufferToBase64url(credential.rawId),
      response: {
        clientDataJSON: bufferToBase64url(credential.response.clientDataJSON),
        attestationObject: bufferToBase64url(credential.response.attestationObject),
      },
      type: credential.type,
      nickname: nickname,
    };

    const completeResp = await fetch('/passkey/register/complete', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(credentialJSON),
    });

    const result = await completeResp.json();
    if (result.success) {
      window.location.reload();
    } else {
      errEl.textContent = result.error || 'Registration failed. Please try again.';
      errEl.classList.remove('d-none');
      btn.disabled = false;
    }
  } catch (err) {
    if (err.name !== 'NotAllowedError') {
      errEl.textContent = err.message || 'Something went wrong. Please try again.';
      errEl.classList.remove('d-none');
    }
    btn.disabled = false;
  }
});

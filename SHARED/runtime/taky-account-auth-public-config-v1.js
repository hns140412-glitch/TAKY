(() => {
'use strict';
const VERSION='2026.09.30-account-auth-public-config-v1';
const GOOGLE_WEB_CLIENT_ID='15791067602-lvao9ohkbj3l5s3clbfb9n106uqssaol.apps.googleusercontent.com';
const APPROVED_ORIGINS=Object.freeze([
  'https://profound-ganache-902032.netlify.app',
  'https://hide-seek-taky.netlify.app',
  'https://cheerful-pothos-d1c3ee.netlify.app'
]);
const apiBaseUrl=typeof window.TAKY_CENTRAL_API_BASE_URL==='string'?window.TAKY_CENTRAL_API_BASE_URL.trim():'';
window.TAKY_ACCOUNT_AUTH_CONFIG=Object.freeze({version:VERSION,googleClientId:GOOGLE_WEB_CLIENT_ID,approvedOrigins:APPROVED_ORIGINS,apiBaseUrl});
})();
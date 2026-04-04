// 测试 SSO Token Exchange
// 运行: node test-sso-token.js

const fetch = require('node-fetch');

const config = {
  ssoBaseUrl: 'https://uat-sso.cheersai.cloud',
  clientId: 'c98f7150fe9c044bf217',
  clientSecret: '13b46d1128c1c0c0d93616a04c76a77570f12f4',
  // 你需要从浏览器获取一个真实的 code
  code: 'YOUR_CODE_HERE',
  redirectUri: 'http://localhost:3000/oauth-callback'
};

async function testTokenExchange() {
  console.log('Testing SSO Token Exchange...\n');
  console.log('Config:', {
    ssoBaseUrl: config.ssoBaseUrl,
    clientId: config.clientId,
    clientSecretLength: config.clientSecret.length,
    redirectUri: config.redirectUri
  });
  console.log('\n');

  const tokenUrl = `${config.ssoBaseUrl}/api/login/oauth/access_token`;
  const authString = Buffer.from(`${config.clientId}:${config.clientSecret}`).toString('base64');
  
  const params = new URLSearchParams();
  params.append('grant_type', 'authorization_code');
  params.append('code', config.code);
  params.append('redirect_uri', config.redirectUri);
  params.append('client_id', config.clientId);
  params.append('client_secret', config.clientSecret);

  console.log('Request URL:', tokenUrl);
  console.log('Request Headers:', {
    'Content-Type': 'application/x-www-form-urlencoded',
    'Authorization': `Basic ${authString}`,
    'Accept': 'application/json'
  });
  console.log('Request Body:', params.toString());
  console.log('\n');

  try {
    const response = await fetch(tokenUrl, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
        'Authorization': `Basic ${authString}`,
        'Accept': 'application/json'
      },
      body: params.toString(),
    });

    console.log('Response Status:', response.status);
    console.log('Response Headers:', Object.fromEntries(response.headers.entries()));
    
    const responseText = await response.text();
    console.log('Response Body:', responseText);
    
    if (response.ok) {
      console.log('\n✅ SUCCESS! Token exchange worked!');
      const data = JSON.parse(responseText);
      console.log('Access Token:', data.access_token?.substring(0, 20) + '...');
    } else {
      console.log('\n❌ FAILED! Token exchange failed.');
      try {
        const errorData = JSON.parse(responseText);
        console.log('Error:', errorData);
      } catch (e) {
        console.log('Raw error:', responseText);
      }
    }
  } catch (error) {
    console.error('Request failed:', error.message);
  }
}

if (config.code === 'YOUR_CODE_HERE') {
  console.log('⚠️  Please update the "code" in this script with a real authorization code.');
  console.log('');
  console.log('To get a code:');
  console.log('1. Visit: http://localhost:3000/signin');
  console.log('2. Click "SSO 登录"');
  console.log('3. Complete SSO authentication');
  console.log('4. Copy the "code" parameter from the callback URL');
  console.log('5. Update this script and run again');
} else {
  testTokenExchange();
}

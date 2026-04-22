#!/usr/bin/env node

/**
 * Validation script to check if all services are running correctly
 * Run this after starting both Express and Flask servers
 * 
 * Usage: node backend/validate-setup.js
 */

const axios = require('axios');

// ANSI color codes for terminal output
const colors = {
  reset: '\x1b[0m',
  green: '\x1b[32m',
  red: '\x1b[31m',
  yellow: '\x1b[33m',
  blue: '\x1b[34m',
  cyan: '\x1b[36m'
};

function log(color, symbol, message) {
  console.log(`${color}${symbol} ${message}${colors.reset}`);
}

async function validateService(name, url, method = 'GET', data = null) {
  try {
    const config = {
      method,
      url,
      timeout: 5000,
      validateStatus: () => true // Don't throw on any status code
    };
    
    if (method === 'POST' && data) {
      config.data = data;
      config.headers = { 'Content-Type': 'application/json' };
    }

    const response = await axios(config);
    
    if (response.status < 300) {
      log(colors.green, '✓', `${name}: Running on ${url}`);
      return true;
    } else if (response.status === 404) {
      log(colors.red, '✗', `${name}: Route not found (404) at ${url}`);
      return false;
    } else if (response.status === 503) {
      log(colors.yellow, '⚠', `${name}: Service unavailable (503) at ${url}`);
      return false;
    } else {
      log(colors.yellow, '⚠', `${name}: Unexpected status ${response.status} at ${url}`);
      return false;
    }
  } catch (error) {
    if (error.code === 'ECONNREFUSED') {
      log(colors.red, '✗', `${name}: Connection refused - is the server running on ${url}?`);
    } else if (error.code === 'ENOTFOUND') {
      log(colors.red, '✗', `${name}: Host not found - check the URL`);
    } else {
      log(colors.red, '✗', `${name}: ${error.message}`);
    }
    return false;
  }
}

async function validateCORS(name, url) {
  try {
    const response = await axios.options(url, {
      timeout: 5000,
      headers: {
        'Origin': 'http://localhost:3000',
        'Access-Control-Request-Method': 'POST',
        'Access-Control-Request-Headers': 'Content-Type'
      }
    });
    
    const corsHeaders = {
      'Access-Control-Allow-Origin': response.headers['access-control-allow-origin'],
      'Access-Control-Allow-Methods': response.headers['access-control-allow-methods'],
      'Access-Control-Allow-Headers': response.headers['access-control-allow-headers']
    };
    
    if (corsHeaders['Access-Control-Allow-Origin']) {
      log(colors.green, '✓', `${name}: CORS headers present`);
      return true;
    } else {
      log(colors.yellow, '⚠', `${name}: CORS headers missing in preflight response`);
      return false;
    }
  } catch (error) {
    log(colors.yellow, '⚠', `${name}: Could not validate CORS - ${error.message}`);
    return false;
  }
}

async function runValidation() {
  console.clear();
  log(colors.blue, '═══', 'SentinelFarm API Validation Script');
  log(colors.blue, '═══', '================================\n');

  const results = {
    express: false,
    flask: false,
    indicesList: false,
    indicesCalculate: false,
    cors: false
  };

  // Check Express server
  log(colors.cyan, '📋', 'Checking Express Server (port 5000)...\n');
  results.express = await validateService('Express Health Check', 'http://localhost:5000/health');
  console.log();

  // Check Flask server
  log(colors.cyan, '📋', 'Checking Flask Server (port 5001)...\n');
  results.flask = await validateService('Flask Health Check', 'http://localhost:5001/health');
  console.log();

  if (results.express) {
    // Check Express indices routes
    log(colors.cyan, '📋', 'Checking Express Indices Routes...\n');
    
    results.indicesList = await validateService(
      'GET /api/indices/list',
      'http://localhost:5000/api/indices/list',
      'GET'
    );
    
    // Only test POST if Flask is running
    if (results.flask) {
      results.indicesCalculate = await validateService(
        'POST /api/indices/calculate (healthcheck)',
        'http://localhost:5000/api/indices/calculate',
        'POST',
        {
          coordinates: [[75.54, 22.71]], // Dummy coordinates
          start_date: '2026-01-01',
          end_date: '2026-01-31',
          index_name: 'NDVI'
        }
      );
    } else {
      log(colors.yellow, '⊘', 'Skipping POST routes test - Flask not running');
    }
    console.log();

    // Check CORS
    log(colors.cyan, '📋', 'Checking CORS Configuration...\n');
    results.cors = await validateCORS(
      'CORS Preflight',
      'http://localhost:5000/api/indices/calculate'
    );
    console.log();
  }

  // Summary
  log(colors.blue, '═══', '================================\n');
  log(colors.cyan, '📊', 'Validation Summary:\n');

  const services = [
    { name: 'Express Server', result: results.express },
    { name: 'Flask Server', result: results.flask },
    { name: 'Indices Routes', result: results.indicesList && results.indicesCalculate },
    { name: 'CORS Configuration', result: results.cors }
  ];

  let allGood = true;
  for (const service of services) {
    if (service.result) {
      log(colors.green, '✓', `${service.name}: OK`);
    } else {
      log(colors.red, '✗', `${service.name}: FAILED`);
      allGood = false;
    }
  }

  console.log();

  if (allGood && results.express && results.flask) {
    log(colors.green, '✓✓✓', 'All systems operational! Your frontend should now work.\n');
  } else {
    log(colors.yellow, '⚠', 'Some services are not running. Please check the setup.\n');
    
    if (!results.express) {
      log(colors.yellow, 'ℹ', 'Express server not running: npm start');
    }
    if (!results.flask) {
      log(colors.yellow, 'ℹ', 'Flask server not running: python app.py');
    }
  }
}

// Run validation
runValidation().catch(console.error);

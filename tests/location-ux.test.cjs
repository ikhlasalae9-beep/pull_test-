// Run: node --test tests/location-ux.test.cjs (uses the installed TypeScript compiler).
const fs = require('node:fs');
const path = require('node:path');
const ts = require('typescript');
const Module = require('node:module');
const assert = require('node:assert/strict');
const { test } = require('node:test');
const root = path.resolve(__dirname, '..');
for (const ext of ['.ts', '.tsx']) require.extensions[ext] = (module, filename) => {
  module._compile(ts.transpileModule(fs.readFileSync(filename, 'utf8'), {
    compilerOptions: { module: ts.ModuleKind.CommonJS, jsx: ts.JsxEmit.React, esModuleInterop: true }
  }).outputText, filename);
};
const resolve = Module._resolveFilename;
Module._resolveFilename = function(name, ...args) {
  return resolve.call(this, name.startsWith('@/') ? path.join(root, name.slice(2)) : name, ...args);
};
const { neighborhoodOptions, compatibleNeighborhood, neighborhoodForApi } = require('../lib/estimation/locations.ts');
const ref = require('../models/neighborhoods_v1.json');
const React = require('react');
const { renderToStaticMarkup } = require('react-dom/server');
const { NeighborhoodSelect } = require('../components/estimation/NeighborhoodSelect.tsx');
for (const city of ['Casablanca', 'Tanger']) test(`${city} options contain exactly its own neighborhoods`, () => {
  assert.deepEqual(neighborhoodOptions(city).map(o => o.value).sort(), [...ref[city]].sort());
  const html = renderToStaticMarkup(React.createElement(NeighborhoodSelect, { city, value: '', onChange() {}, locale: 'fr' }));
  const values = [...html.matchAll(/<option value="([^"]*)"/g)].map(m => m[1]);
  assert.equal(values.length, ref[city].length + 1);
  assert.equal(values.at(-1), '');
});
test('changing city clears an incompatible selection', () => {
  const casaOnly = ref.Casablanca.find(n => !ref.Tanger.includes(n));
  assert.ok(casaOnly);
  assert.equal(compatibleNeighborhood('Tanger', casaOnly), '');
  assert.equal(neighborhoodForApi('Tanger', casaOnly), 'Rare');
});
test('search casing affects filtering only; arbitrary strings cannot be selected', () => {
  const canonical = ref.Casablanca.find(n => n !== n.toUpperCase());
  assert.ok(neighborhoodOptions('Casablanca', canonical.toUpperCase()).some(o => o.value === canonical));
  assert.equal(neighborhoodForApi('Casablanca', 'arbitrary typed neighborhood'), 'Rare');
  assert.equal(neighborhoodForApi('Casablanca', canonical.toUpperCase()), ref.Casablanca.includes(canonical.toUpperCase()) ? canonical.toUpperCase() : 'Rare');
  const html = renderToStaticMarkup(React.createElement(NeighborhoodSelect, { city:'Casablanca',value:'',onChange(){},locale:'fr' }));
  assert.match(html, /<select id="quartier"/);
  assert.doesNotMatch(html, /<input[^>]*id="quartier"/);
});
test('canonical value reaches the API request unchanged; Other uses the fitted rare token', async () => {
  const { predictProperty } = require('../lib/api/client.ts');
  const previous = global.fetch;
  const canonical = ref.Casablanca[0];
  let received;
  global.fetch = async (url, options) => { received = JSON.parse(options.body); return { ok:true, json:async () => ({estimated_price_mad:1000000}) }; };
  try {
    await predictProperty({ city:'Casablanca', neighborhood:neighborhoodForApi('Casablanca',canonical) });
    assert.equal(received.neighborhood, canonical);
    await predictProperty({ city:'Casablanca', neighborhood:neighborhoodForApi('Casablanca','') });
    assert.equal(received.neighborhood, 'Rare');
  } finally { global.fetch = previous; }
});
test('only Appartement remains enabled', () => {
  const { PROPERTY_TYPES_CONFIG } = require('../config/estimator.config.ts');
  assert.deepEqual(PROPERTY_TYPES_CONFIG.filter(o => !o.disabled).map(o => o.value), ['appartement']);
  for (const type of ['villa','duplex','studio']) assert.equal(PROPERTY_TYPES_CONFIG.find(o => o.value === type).disabled, true);
});

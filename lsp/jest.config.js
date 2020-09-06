const func = require('@jupyterlab/testutils/lib/jest-config');
const upstream = func('data-vault-lsp', __dirname);

const reuseFromUpstream = [
  'moduleFileExtensions',
  'moduleNameMapper',
  'reporters',
  'setupFiles',
  'setupFilesAfterEnv',
  'testPathIgnorePatterns'
];

let local = {
  globals: { 'ts-jest': { tsConfig: 'tsconfig.json' } },
  testRegex: `.*\.spec\.tsx?$`,
  transform: {
    '\\.(ts|tsx)?$': 'ts-jest',
    '\\.(js|jsx)?$': './transform.js'
  },
  transformIgnorePatterns: [
    '/node_modules/(?!((@jupyterlab/.*)|(@krassowski/.*))/)'
  ]
};

for (const option of reuseFromUpstream) {
  local[option] = upstream[option];
}

module.exports = local;

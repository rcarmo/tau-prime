import globals from 'globals';

export default [
  {
    files: ['static/js/**/*.js'],
    ignores: [
      'static/js/marked.min.js',
      'static/js/vendor/**',
    ],
    languageOptions: {
      ecmaVersion: 2022,
      sourceType: 'module',
      globals: {
        ...globals.browser,
      },
    },
    rules: {
      'no-unused-vars': 'off',
    },
  },
];

/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ["./src/renderer/**/*.{html,tsx}"],
  theme: {
    extend: {
      gridTemplateColumns: {
        "auto-fill-100": "repeat(auto-fill, minmax(200px, 1fr))",
        "auto-fit-100": "repeat(auto-fit, minmax(200px, 1fr))",
      },
    },
  },
  plugins: [],
}

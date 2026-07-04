/** @type {import('next').NextConfig} */
const nextConfig = {
  output: "standalone",
  transpilePackages: ["@loppis/shared"],
};

module.exports = nextConfig;
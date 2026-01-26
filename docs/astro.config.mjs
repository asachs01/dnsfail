// @ts-check
import { defineConfig } from 'astro/config';
import starlight from '@astrojs/starlight';

// https://astro.build/config
export default defineConfig({
	site: 'https://asachs01.github.io/dnsfail',
	base: 'dnsfail',
	trailingSlash: 'always',
	integrations: [
		starlight({
			title: 'DNS Incident Timer',
			description: 'A Raspberry Pi-based incident timer that tracks DNS failures with LED display and audio alerts.',
			social: [
				{ icon: 'github', label: 'GitHub', href: 'https://github.com/asachs01/dnsfail' },
			],
			sidebar: [
				{
					label: 'Getting Started',
					items: [
						{ label: 'Introduction', link: '/dnsfail/getting-started/introduction/' },
						{ label: 'Hardware Requirements', link: '/dnsfail/getting-started/hardware/' },
						{ label: 'Quick Start', link: '/dnsfail/getting-started/quick-start/' },
					],
				},
				{
					label: 'Installation',
					items: [
						{ label: 'Native Installation', link: '/dnsfail/installation/native/' },
						{ label: 'Docker Deployment', link: '/dnsfail/installation/docker/' },
					],
				},
				{
					label: 'Configuration',
					items: [
						{ label: 'Configuration Options', link: '/dnsfail/configuration/options/' },
						{ label: 'GPIO Setup', link: '/dnsfail/configuration/gpio/' },
						{ label: 'Audio Setup', link: '/dnsfail/configuration/audio/' },
						{ label: 'Web Interface', link: '/dnsfail/configuration/web-interface/' },
					],
				},
				{
					label: 'Troubleshooting',
					items: [
						{ label: 'Common Issues', link: '/dnsfail/troubleshooting/common-issues/' },
						{ label: 'Docker Issues', link: '/dnsfail/troubleshooting/docker/' },
					],
				},
				{
					label: 'Reference',
					items: [
						{ label: 'Architecture', link: '/dnsfail/reference/architecture/' },
						{ label: 'API', link: '/dnsfail/reference/api/' },
					],
				},
			],
			customCss: ['./src/styles/custom.css'],
		}),
	],
});

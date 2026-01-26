// @ts-check
import { defineConfig } from 'astro/config';
import starlight from '@astrojs/starlight';

// https://astro.build/config
export default defineConfig({
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
						{ label: 'Introduction', slug: 'getting-started/introduction' },
						{ label: 'Hardware Requirements', slug: 'getting-started/hardware' },
						{ label: 'Quick Start', slug: 'getting-started/quick-start' },
					],
				},
				{
					label: 'Installation',
					items: [
						{ label: 'Native Installation', slug: 'installation/native' },
						{ label: 'Docker Deployment', slug: 'installation/docker' },
					],
				},
				{
					label: 'Configuration',
					items: [
						{ label: 'Configuration Options', slug: 'configuration/options' },
						{ label: 'GPIO Setup', slug: 'configuration/gpio' },
						{ label: 'Audio Setup', slug: 'configuration/audio' },
						{ label: 'Web Interface', slug: 'configuration/web-interface' },
					],
				},
				{
					label: 'Troubleshooting',
					items: [
						{ label: 'Common Issues', slug: 'troubleshooting/common-issues' },
						{ label: 'Docker Issues', slug: 'troubleshooting/docker' },
					],
				},
				{
					label: 'Reference',
					items: [
						{ label: 'Architecture', slug: 'reference/architecture' },
						{ label: 'API', slug: 'reference/api' },
					],
				},
			],
			customCss: ['./src/styles/custom.css'],
		}),
	],
});

/**
 * AppAPI embedded handoff page for opening a validated Google Workspace URL.
 * The target is supplied as URL-safe base64 in the path by the ExApp backend.
 */
(() => {
	'use strict'

	const APP_PATH = '/embedded/io-google-workspace-redirect/workspace/open/'

	function decodeTargetFromPath() {
		const markerIndex = window.location.pathname.indexOf(APP_PATH)
		if (markerIndex === -1) {
			return null
		}

		const token = window.location.pathname.slice(markerIndex + APP_PATH.length).split('/')[0]
		if (!token || !/^[A-Za-z0-9_-]+$/.test(token)) {
			return null
		}

		try {
			const base64 = token.replace(/-/g, '+').replace(/_/g, '/')
			const padded = base64 + '='.repeat((4 - (base64.length % 4)) % 4)
			return atob(padded)
		} catch (error) {
			console.error('[IO Google Workspace Redirect] Invalid handoff token', error)
			return null
		}
	}

	function isAllowedGoogleUrl(value) {
		try {
			const url = new URL(value)
			const allowedPaths = [
				/^\/document\/d\/[A-Za-z0-9_-]{10,256}\/edit$/,
				/^\/spreadsheets\/d\/[A-Za-z0-9_-]{10,256}\/edit$/,
				/^\/presentation\/d\/[A-Za-z0-9_-]{10,256}\/edit$/,
			]
			const queryKeys = [...url.searchParams.keys()]

			return url.protocol === 'https:'
				&& url.hostname === 'docs.google.com'
				&& allowedPaths.some((pattern) => pattern.test(url.pathname))
				&& queryKeys.every((key) => key === 'resourcekey')
		} catch (error) {
			return false
		}
	}

	function createElement(tag, text, styles = {}) {
		const element = document.createElement(tag)
		if (text) {
			element.textContent = text
		}
		Object.assign(element.style, styles)
		return element
	}

	function renderPage(target) {
		const content = document.getElementById('content') || document.body
		content.replaceChildren()

		const card = createElement('main', '', {
			maxWidth: '560px',
			margin: '64px auto',
			padding: '32px',
			textAlign: 'center',
			background: 'var(--color-main-background)',
			border: '1px solid var(--color-border)',
			borderRadius: '16px',
		})
		const title = createElement('h2', 'IO Google Workspace')
		const message = createElement(
			'p',
			target
				? 'O documento está pronto para ser aberto em uma nova aba.'
				: 'Use a ação “Abrir no Google Workspace” no menu de um arquivo .gdoc, .gsheet ou .gslides.',
			{ margin: '16px 0 24px' },
		)

		card.append(title, message)
		if (target) {
			const link = createElement('a', 'Abrir no Google Workspace', {
				display: 'inline-block',
				padding: '12px 20px',
				color: 'var(--color-primary-text)',
				background: 'var(--color-primary-element)',
				borderRadius: '24px',
				textDecoration: 'none',
			})
			link.href = target
			link.target = '_blank'
			link.rel = 'noopener noreferrer'
			link.addEventListener('click', () => window.setTimeout(() => window.history.back(), 300))
			card.append(link)
		}
		content.append(card)
	}

	function openTarget(target) {
		renderPage(target)
		const opened = window.open(target, '_blank')
		if (opened) {
			try {
				opened.opener = null
			} catch (error) {
				// Cross-origin protections may prevent access; rel=noopener remains on the fallback link.
			}
			window.setTimeout(() => window.history.back(), 300)
		}
	}

	const target = decodeTargetFromPath()
	if (target && isAllowedGoogleUrl(target)) {
		openTarget(target)
	} else {
		renderPage(null)
	}
})()


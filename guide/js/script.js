/* ai.zipガイド版: 画像拡大・スマホメニュー */
function initGuide() {
  if (window.__guideInitialized) return;
  window.__guideInitialized = true;

  const toggle = document.querySelector('.menu-toggle');
  const nav = document.querySelector('.site-nav');

  toggle?.addEventListener('click', () => {
    const opened = nav.classList.toggle('open');
    toggle.setAttribute('aria-expanded', String(opened));
    toggle.setAttribute('aria-label', opened ? 'メニューを閉じる' : 'メニューを開く');
  });

  const current = location.pathname.split('/').pop().replace('.html', '') || 'index';
  document.querySelectorAll('.site-nav a').forEach(a => {
    if (a.dataset.page === current) a.classList.add('active');
  });

  const lightbox = document.querySelector('.lightbox');
  const enlarged = lightbox?.querySelector('img');

  function closeBox() {
    if (!lightbox) return;
    lightbox.hidden = true;
    enlarged?.removeAttribute('src');
    document.body.style.overflow = '';
  }

  lightbox?.querySelector('button')?.addEventListener('click', closeBox);
  lightbox?.addEventListener('click', e => {
    if (e.target === lightbox) closeBox();
  });
  document.addEventListener('keydown', e => {
    if (e.key === 'Escape' && lightbox && !lightbox.hidden) closeBox();
  });

  document.querySelectorAll('.media-frame img').forEach(img => {
    img.addEventListener('click', () => {
      if (!lightbox || !enlarged) return;
      enlarged.src = img.currentSrc || img.src;
      lightbox.hidden = false;
      document.body.style.overflow = 'hidden';
    });
  });

  // 元の画像パスが存在する場合は、画像を読み込みます。
  document.querySelectorAll('.media-frame[data-media="image"][data-src]').forEach(frame => {
    if (frame.querySelector('img')) return;
    const img = new Image();
    img.alt = '操作画面のスクリーンショット';
    img.onload = () => {
      frame.replaceChildren(img);
      img.addEventListener('click', () => {
        if (!lightbox || !enlarged) return;
        enlarged.src = img.src;
        lightbox.hidden = false;
        document.body.style.overflow = 'hidden';
      });
    };
    img.src = frame.dataset.src;
  });
}

if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', initGuide);
} else {
  initGuide();
}

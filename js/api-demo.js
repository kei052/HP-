(() => {
  'use strict';
  const base = ''; // Same-origin API exposed by backend/app_server.py
  const el = id => document.getElementById(id);
  let courses = [];
  const text = (tag, value) => { const node = document.createElement(tag); node.textContent = value; return node; };
  async function request(path, options) {
    const response = await fetch(base + path, options);
    if (!response.ok) throw new Error(`APIエラー (${response.status})`);
    return response.json();
  }
  function showError(error) {
    el('status').className = 'error';
    el('status').textContent = `APIに接続できません。バックエンドを起動して再読み込みしてください。（${error.message}）`;
  }
  function checkboxes(id) {
    const container = el(id); container.replaceChildren();
    for (const course of courses) {
      const label = document.createElement('label'), input = document.createElement('input');
      input.type = 'checkbox'; input.value = course.course_id;
      label.append(input, document.createTextNode(` ${course.course_name}`)); container.append(label);
    }
  }
  function selectOptions(id, items, key, name) {
    const select = el(id); select.replaceChildren();
    const placeholder = text('option', '選択してください'); placeholder.value = ''; select.append(placeholder);
    for (const item of items) { const opt = text('option', item[name]); opt.value = item[key]; select.append(opt); }
    select.disabled = false;
  }
  function list(container, heading, items) {
    container.append(text('h3', heading)); const ul = document.createElement('ul');
    if (!items.length) ul.append(text('li', '該当なし'));
    for (const value of items) ul.append(text('li', value)); container.append(ul);
  }
  async function details(type) {
    const select = el(type), target = el(type === 'jobs' ? 'job-detail' : 'qualification-detail');
    target.replaceChildren(); if (!select.value) return;
    try {
      const result = await request(`/${type}/${encodeURIComponent(select.value)}`);
      if (type === 'jobs') {
        list(target, '関連講義', result.courses.map(c => `${c.course_name}（スコア ${c.score}）`));
        list(target, '関連資格', result.qualifications.map(q => q.qualification_name));
      } else {
        list(target, '関連講義', result.courses.map(c => c.course_name));
        list(target, '関連職業', result.jobs.map(j => j.job_name));
      }
    } catch (error) { showError(error); }
  }
  function selected(id) { return [...el(id).querySelectorAll('input:checked')].map(input => input.value); }
  function resultTable(root, title, before, after, key, name, recommendations) {
    root.append(text('h3', title)); const table = document.createElement('table');
    const header = document.createElement('tr'); for (const value of ['名前', '履修済み', '候補追加後', '未選択の講義']) header.append(text('th', value)); table.append(header);
    const afterById = new Map(after.map(item => [item[key], item]));
    const names = new Map(courses.map(c => [c.course_id, c.course_name]));
    for (const item of before) {
      const updated = afterById.get(item[key]); const row = document.createElement('tr');
      for (const value of [item[name], `${item.rate}%`, `${updated.rate}%`, updated[recommendations].map(id => names.get(id) || id).join('、') || 'なし']) row.append(text('td', value));
      table.append(row);
    }
    root.append(table);
  }
  async function diagnose() {
    el('diagnose').disabled = true;
    try {
      const result = await request('/simulation', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({completed_course_ids:selected('completed'),candidate_course_ids:selected('candidate')})});
      const root = el('results'); root.replaceChildren();
      resultTable(root, '職業', result.completed.jobs, result.simulated.jobs, 'job_id', 'job_name', 'recommended_course_ids');
      resultTable(root, '資格', result.completed.qualifications, result.simulated.qualifications, 'qualification_id', 'qualification_name', 'missing_course_ids');
      el('status').className = ''; el('status').textContent = 'APIに接続しています。';
    } catch (error) { showError(error); } finally { el('diagnose').disabled = false; }
  }
  async function init() {
    try {
      const [courseData, jobData, qualificationData] = await Promise.all([request('/courses'),request('/jobs'),request('/qualifications')]);
      courses = courseData.courses; checkboxes('completed'); checkboxes('candidate');
      selectOptions('jobs',jobData.jobs,'job_id','job_name');
      selectOptions('qualifications',qualificationData.qualifications,'qualification_id','qualification_name');
      el('diagnose').disabled = false; el('status').textContent = 'APIに接続しています。';
    } catch (error) { showError(error); }
  }
  el('diagnose').addEventListener('click', diagnose);
  el('jobs').addEventListener('change', () => details('jobs'));
  el('qualifications').addEventListener('change', () => details('qualifications'));
  init();
})();

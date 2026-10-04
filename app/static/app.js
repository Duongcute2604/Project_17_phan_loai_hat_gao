/* =====================================================================
   Rice Classification - Frontend
   Tu pham nghiep vu don gian, khong dung framework.
   ===================================================================== */

/* --- Dinh nghia API --- */
const API = {
  health:      '/api/health',
  valueHelp:   '/api/value-help',
  classify:    '/api/rice-classify',
  modelCard:   '/api/model-card',
};

/* Tu khoa mo ta dac trung (dung cho placeholder va giải thích) */
const FEATURE_INFO = {
  Area:                { label: 'Area',                desc: 'Diện tích hạt gạo' },
  Perimeter:           { label: 'Perimeter',           desc: 'Chu vi hạt gạo' },
  Major_Axis_Length:   { label: 'Major Axis Length',   desc: 'Chiều dài trục lớn nhất' },
  Minor_Axis_Length:   { label: 'Minor Axis Length',   desc: 'Chiều dài trục nhỏ nhất' },
  Eccentricity:        { label: 'Eccentricity',        desc: 'Độ lệch tâm' },
  Convex_Area:         { label: 'Convex Area',         desc: 'Diện tích bao lồi' },
  Extent:              { label: 'Extent',              desc: 'Tỉ lệ diện tích thật / bao lồi' },
};

/* Khoang gia tri thay the (fallback khi API chua san) */
const FALLBACK_RANGE = {
  Area:              { min: 7000,  max: 19500, unit: 'pixel²' },
  Perimeter:         { min: 340,   max: 570,   unit: 'pixel' },
  Major_Axis_Length: { min: 125,   max: 255,   unit: 'pixel' },
  Minor_Axis_Length: { min: 55,    max: 112,   unit: 'pixel' },
  Eccentricity:      { min: 0.77,  max: 0.96,  unit: '(0–1)' },
  Convex_Area:       { min: 7000,  max: 19500, unit: 'pixel²' },
  Extent:            { min: 0.40,  max: 0.94,  unit: '(0–1)' },
};

/* Gia tri vi du lay tu dong lieu that */
const EXAMPLE = {
  Area: 15231,
  Perimeter: 525.579,
  Major_Axis_Length: 229.750,
  Minor_Axis_Length: 85.094,
  Eccentricity: 0.9289,
  Convex_Area: 15617,
  Extent: 0.5729,
};

let valueHelp = FALLBACK_RANGE;

/* =====================================================================
   Tien ich
   ===================================================================== */
const $ = (id) => document.getElementById(id);

function show(el) { el.classList.remove('hidden'); }
function hide(el) { el.classList.add('hidden'); }

async function getJSON(url) {
  const response = await fetch(url);
  if (!response.ok) throw new Error(`${url} -> ${response.status}`);
  return response.json();
}

/* =====================================================================
   1. DIEU HUONG
   ===================================================================== */
document.querySelectorAll('nav button').forEach((button) => {
  button.addEventListener('click', () => {
    document.querySelectorAll('nav button').forEach((b) => b.classList.remove('active'));
    button.classList.add('active');

    document.querySelectorAll('.screen').forEach((s) => s.classList.remove('active'));
    $(`screen-${button.dataset.screen}`).classList.add('active');

    if (button.dataset.screen === 'dashboard') loadDashboard();
  });
});

/* =====================================================================
   2. MAN HINH 1 - BANG DAC TRUNG
   ===================================================================== */
async function loadIntro() {
  try {
    valueHelp = await getJSON(API.valueHelp);
  } catch (error) {
    console.warn('Khong tai duoc value-help, dung gia tri mac dinh', error);
    valueHelp = FALLBACK_RANGE;
  }

  const tbody = document.querySelector('#feature-table tbody');
  tbody.innerHTML = Object.entries(FEATURE_INFO).map(([key, info]) => {
    const range = valueHelp[key] || FALLBACK_RANGE[key];
    const rangeText = `${range.min} – ${range.max} ${range.unit}`;
    return `<tr>
      <td><code>${key}</code></td>
      <td>${info.desc}</td>
      <td>${range.unit}</td>
      <td>${rangeText}</td>
    </tr>`;
  }).join('');

  buildForm();
}

/* =====================================================================
   3. MAN HINH 2 - FORM
   ===================================================================== */
function buildForm() {
  const grid = $('form-grid');

  grid.innerHTML = Object.entries(FEATURE_INFO).map(([key, info]) => {
    const range = valueHelp[key] || FALLBACK_RANGE[key];
    return `
      <div class="field" data-feature="${key}">
        <label for="in-${key}">${info.label}</label>
        <div class="desc">${info.desc}</div>
        <input type="number" step="any" id="in-${key}" name="${key}"
               placeholder="ví dụ: ${range.min} – ${range.max}">
        <div class="range">Đơn vị: ${range.unit} · khoảng trong dữ liệu: ${range.min} – ${range.max}</div>
        <div class="err"></div>
      </div>`;
  }).join('');
}

function clearErrors() {
  document.querySelectorAll('.field').forEach((f) => {
    f.classList.remove('invalid');
    f.querySelector('.err').textContent = '';
  });
  hide($('form-errors'));
}

function showFieldError(key, message) {
  const field = document.querySelector(`.field[data-feature="${key}"]`);
  if (!field) return;
  field.classList.add('invalid');
  field.querySelector('.err').textContent = message;
}

function showFormErrors(messages) {
  const box = $('form-errors');
  box.innerHTML = `<strong>Không thể phân loại — vui lòng sửa:</strong>
    <ul>${messages.map((m) => `<li>${m}</li>`).join('')}</ul>`;
  show(box);
}

/* --- Kiem tra phia trinh duoc --- */
function validate() {
  clearErrors();
  const errors = [];

  Object.keys(FEATURE_INFO).forEach((key) => {
    const input = $(`in-${key}`);
    const raw = input.value.trim();

    if (raw === '') {
      showFieldError(key, 'Bắt buộc nhập — không tự dùng giá trị mặc định.');
      errors.push(`<b>${FEATURE_INFO[key].label}</b>: chưa nhập`);
      return;
    }

    const value = Number(raw);
    if (Number.isNaN(value)) {
      showFieldError(key, 'Phải là số.');
      errors.push(`<b>${FEATURE_INFO[key].label}</b>: không phải số`);
      return;
    }

    if (value <= 0 && key !== 'Eccentricity' && key !== 'Extent') {
      showFieldError(key, 'Phải lớn hơn 0.');
      errors.push(`<b>${FEATURE_INFO[key].label}</b>: phải lớn hơn 0`);
      return;
    }

    if ((key === 'Eccentricity' || key === 'Extent') && (value < 0 || value > 1)) {
      showFieldError(key, 'Phải nằm trong khoảng 0 – 1.');
      errors.push(`<b>${FEATURE_INFO[key].label}</b>: phải trong khoảng 0–1, nhận ${value}`);
    }
  });

  return errors;
}

function collectData() {
  const data = {};
  Object.keys(FEATURE_INFO).forEach((key) => {
    data[key] = Number($(`in-${key}`).value);
  });
  return data;
}

/* --- Gui yeu cau phan loai --- */
$('predict-form').addEventListener('submit', async (event) => {
  event.preventDefault();

  const errors = validate();
  if (errors.length > 0) {
    showFormErrors(errors);
    hide($('result'));
    hide($('result-warnings'));
    hide($('result-note'));
    hide($('rule-card'));
    return;
  }

  const button = $('btn-submit');
  button.disabled = true;
  button.textContent = 'Đang phân loại…';

  try {
    const response = await fetch(API.classify, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(collectData()),
    });

    if (!response.ok) {
      const detail = await response.json().catch(() => ({}));
      showFormErrors([`Máy chủ báo lỗi ${response.status}: ${detail.detail || 'không rõ nguyên nhân'}`]);
      return;
    }

    renderResult(await response.json());
  } catch (error) {
    showFormErrors([`Không kết nối được máy chủ: ${error.message}`]);
  } finally {
    button.disabled = false;
    button.textContent = 'Phân loại';
  }
});

/* --- Hien thi ket qua --- */
function renderResult(data) {
  const box = $('result');
  box.className = `result ${data.prediction.toLowerCase()}`;
  $('result-value').textContent = data.prediction;

  const percent = (data.confidence * 100).toFixed(1);
  $('result-conf').innerHTML =
    `Độ tin cậy <strong>${percent}%</strong> · ` +
    `<code>${data.rule_applied.length - 1}</code> điều kiện được áp dụng`;

  // Thanh xac suat
  const cammeo = data.probabilities.Cammeo;
  const osmancik = data.probabilities.Osmancik;
  $('bar-cammeo').style.width = `${cammeo * 100}%`;
  $('bar-osmancik').style.width = `${osmancik * 100}%`;
  $('bar-cammeo-txt').textContent = `${(cammeo * 100).toFixed(1)}%`;
  $('bar-osmancik-txt').textContent = `${(osmancik * 100).toFixed(1)}%`;

  show(box);

  // Canh bao ngoai mien
  const warnBox = $('result-warnings');
  if (data.warnings && data.warnings.length > 0) {
    warnBox.className = 'alert warn';
    warnBox.innerHTML = '<strong>Cảnh báo: giá trị nằm ngoài vùng dữ liệu gốc</strong>' +
      `<ul>${data.warnings.map((w) => `<li>${w.message}</li>`).join('')}</ul>` +
      '<p style="margin:0.4rem 0 0;font-size:0.84rem">' +
      'Mô hình vẫn trả lời, nhưng kết quả không đáng tin cho các hạt gạo bất thường như vậy. ' +
      'Hãy kiểm tra lại phép đo.</p>';
    show(warnBox);
  } else {
    hide(warnBox);
  }

  // Canh bao do tin cay thap
  const noteBox = $('result-note');
  if (data.low_confidence) {
    noteBox.className = 'alert warn';
    noteBox.innerHTML = `<strong>Độ tin cậy thấp (${percent}%).</strong> ${data.note}`;
    show(noteBox);
  } else {
    noteBox.className = 'alert info';
    noteBox.innerHTML = data.note;
    show(noteBox);
  }

  // Quy tac da ap dung
  $('rule-text').innerHTML = data.rule_applied
    .map((step, i) =>
      i === data.rule_applied.length - 1
        ? `<span class="step">${step}</span>`
        : step
    ).join('\n');
  show($('rule-card'));
}

/* --- Nut phu tro --- */
$('btn-example').addEventListener('click', () => {
  clearErrors();
  Object.entries(EXAMPLE).forEach(([key, value]) => { $(`in-${key}`).value = value; });
  hide($('form-errors'));
  hide($('result'));
  hide($('result-warnings'));
  hide($('result-note'));
  hide($('rule-card'));
});

$('btn-clear').addEventListener('click', () => {
  clearErrors();
  Object.keys(FEATURE_INFO).forEach((key) => { $(`in-${key}`).value = ''; });
  hide($('form-errors'));
  hide($('result'));
  hide($('result-warnings'));
  hide($('result-note'));
  hide($('rule-card'));
});

/* =====================================================================
   4. MAN HINH 3 - DASHBOARD
   ===================================================================== */
let dashboardLoaded = false;

async function loadDashboard() {
  if (dashboardLoaded) return;

  try {
    const card = await getJSON(API.modelCard);
    dashboardLoaded = true;
    renderModelCard(card);
  } catch (error) {
    $('model-card').innerHTML =
      `<div class="alert danger">Không tải được model card: ${error.message}</div>`;
  }
}

function pct(value) { return (value * 100).toFixed(2) + '%'; }

function renderModelCard(card) {
  const m = card.metrics_test;
  const v = card.metrics_validation;
  const stability = card.seed_stability;

  $('model-card').innerHTML = `
    <table>
      <thead>
        <tr><th>Chỉ số</th><th class="num">Validation</th><th class="num">Test</th></tr>
      </thead>
      <tbody>
        <tr><td>Accuracy</td><td class="num">${pct(v.accuracy)}</td><td class="num"><strong>${pct(m.accuracy)}</strong></td></tr>
        <tr><td>Precision (Cammeo)</td><td class="num">${pct(v.precision)}</td><td class="num">${pct(m.precision)}</td></tr>
        <tr><td>Recall (Cammeo)</td><td class="num">${pct(v.recall)}</td><td class="num">${pct(m.recall)}</td></tr>
        <tr><td>F1 (Cammeo)</td><td class="num">${pct(v.f1)}</td><td class="num"><strong>${pct(m.f1)}</strong></td></tr>
        <tr><td>ROC-AUC</td><td class="num">${v.roc_auc.toFixed(4)}</td><td class="num"><strong>${m.roc_auc.toFixed(4)}</strong></td></tr>
      </tbody>
    </table>

    <h3>Cấu hình mô hình</h3>
    <p class="lead" style="margin:0">
      <code>${card.model.type}</code> ·
      <code>ccp_alpha=${card.model.ccp_alpha}</code> ·
      <code>random_state=${card.model.random_state}</code> ·
      cây có <strong>${card.model.n_leaves} lá</strong>
    </p>

    <h3>Độ ổn định qua 5 cách chia tập</h3>
    <p class="lead" style="margin:0">
      F1 dao động ${Math.min(...stability.f1_scores).toFixed(4)} – ${Math.max(...stability.f1_scores).toFixed(4)}
      (độ lệch chuẩn ${stability.std.toFixed(4)}) → kết quả không phụ thuộc may rủi.
    </p>

    <h3>Dùng để làm gì</h3>
    <ul>${card.intended_use.map((u) => `<li>${u}</li>`).join('')}</ul>

    <h3>Giới hạn</h3>
    <div class="alert warn">
      <ul class="limitations">
        ${card.limitations.map((l) => `<li>${l}</li>`).join('')}
      </ul>
    </div>

    <h3>Không dùng để làm gì</h3>
    <div class="alert danger">
      <ul class="limitations">
        ${card.not_intended_use.map((u) => `<li><strong>${u}</strong></li>`).join('')}
      </ul>
    </div>`;

  renderConfusion(card.confusion_matrix_test);
  $('tree-rules').textContent = card.tree_rules || '(chưa có)';
  loadExperiments();
}

/* --- Ket qua 4 thi nghiem bat buoc ---
   So lieu lay truc tiep tu file reports/*.csv, da chay bang
   src/train.py va src/evaluate.py voi random_state=42. */
function loadExperiments() {
  const box = $('experiments');
  let html = '';

    html += `
      <h3>Thí nghiệm 1 — Độ chính xác theo max_depth</h3>
      <p class="lead">
        Cây không giới hạn đạt 100% trên tập train nhưng chỉ 89.86% trên validation.
        Khoảng cách 10.14 điểm phần trăm là <strong>dấu hiệu quá khớp</strong>.
      </p>`;

    html += `
      <h3>Thí nghiệm 2 — Cắt tỉa bằng ccp_alpha (5-fold CV)</h3>
      <p class="lead">
        Cắt tỉa rút cây từ <strong>190 lá xuống 4 lá</strong> mà F1 tăng từ 0.8757 lên 0.9168.
        Đây là bằng chứng rõ nhất cho thấy bỏ nhánh thừa làm mô hình tốt hơn.
      </p>`;

    html += `
      <h3>Thí nghiệm 3 — Cây đơn và rừng ngẫu nhiên</h3>
      <table>
        <thead>
          <tr><th>Mô hình</th><th class="num">Acc</th><th class="num">F1</th><th class="num">Train (s)</th><th>Giai thích</th></tr>
        </thead>
        <tbody>
          <tr>
            <td>Cây cắt tỉa <em>(mô hình chính)</em></td>
            <td class="num">0.9318</td>
            <td class="num">0.9199</td>
            <td class="num">0.019</td>
            <td>Đọc được toàn bộ quy tắc</td>
          </tr>
          <tr>
            <td>Rừng 100 cây</td>
            <td class="num">0.9301</td>
            <td class="num">0.9184</td>
            <td class="num">0.227</td>
            <td>Không có quy tắc đơn để đọc</td>
          </tr>
        </tbody>
      </table>
      <p class="lead" style="margin-top:0.6rem">
        Rừng không tốt hơn mà chậm hơn 12 lần. Với điểm số tương đương,
        <strong>cây đơn là lựa chọn đúng</strong>.
      </p>`;

    html += `
      <h3>Thí nghiệm 4 — Phân tích lỗi</h3>
      <p class="lead">
        Trên tập kiểm thử có 52 mẫu sai (9.09%). Trong đó lỗi bỏ sót Cammeo
        chiếm 60%, cho thấy mô hình nghiêng về lớp đông hơn.
        Không đặc trưng nào phân biệt rõ mẫu sai và mẫu đúng — chứng tỏ các mẫu sai
        nằm ở <strong>vùng chồng lấn thật sự</strong> giữa hai giống, không phải lỗi kỹ thuật.
      </p>`;

  box.innerHTML = html;
}

function renderConfusion(cm) {
  const [cammeo, osmancik] = cm.labels;
  const cells = [
    { v: cm.tn, label: 'Dùng', cls: 'good', note: 'Dùng' },
    { v: cm.fp, label: 'Sai', cls: 'bad',  note: `Dự kiểu ${osmancik}, thực ra ${cammeo}` },
    { v: cm.fn, label: 'Sai', cls: 'bad',  note: `Dự kiểu ${cammeo}, thực ra ${osmancik}` },
    { v: cm.tp, label: 'Dùng', cls: 'good', note: 'Dùng' },
  ];

  $('confusion').innerHTML = `
    <table>
      <thead>
        <tr>
          <th></th>
          <th>Dự đoán<br>${cammeo}</th>
          <th>Dự đoán<br>${osmancik}</th>
        </tr>
      </thead>
      <tbody>
        <tr>
          <td class="label-cell">Thực tế<br>${cammeo}</td>
          <td class="good">${cm.tn}</td>
          <td class="bad">${cm.fp}</td>
        </tr>
        <tr>
          <td class="label-cell">Thực tế<br>${osmancik}</td>
          <td class="bad">${cm.fn}</td>
          <td class="good">${cm.tp}</td>
        </tr>
      </tbody>
    </table>
    <p class="lead" style="margin-top:0.8rem">
      <span style="color:#16a34a">■ Xanh</span> = dự đoán đúng ·
      <span style="color:#dc2626">■ Đỏ</span> = dự đoán sai ·
      Tổng sai: <strong>${cm.fp + cm.fn} / ${cm.tp + cm.fn + cm.fp + cm.tn}</strong>
    </p>`;
}

/* =====================================================================
   Khoi dong
   ===================================================================== */
loadIntro();

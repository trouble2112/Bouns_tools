// ============ SQLite版本 - API数据存储 ============
class APIClient {
    constructor() {
        this.baseURL = window.location.origin;
    }
    
    async request(method, path, data = null) {
        const options = {
            method: method,
            headers: {
                'Content-Type': 'application/json',
            }
        };
        
        if (data) {
            options.body = JSON.stringify(data);
        }
        
        try {
            const response = await fetch(`${this.baseURL}${path}`, options);
            const result = await response.json();
            
            if (!response.ok) {
                throw new Error(result.message || `HTTP ${response.status}`);
            }
            
            return result;
        } catch (error) {
            console.error('API请求失败:', error);
            throw error;
        }
    }
    
    // 人员相关API
    async getPersons() {
        return await this.request('GET', '/api/persons');
    }
    
    async createPerson(data) {
        return await this.request('POST', '/api/persons', data);
    }
    
    async updatePerson(id, data) {
        return await this.request('PUT', `/api/persons/${id}`, data);
    }
    
    async deletePerson(id) {
        return await this.request('DELETE', `/api/persons/${id}`);
    }
    
    // 参数相关API
    async getParams() {
        return await this.request('GET', '/api/params');
    }
    
    async updateParams(data) {
        return await this.request('POST', '/api/params', data);
    }
}

// 全局变量
let api = new APIClient();
let persons = [];
let params = {
    coefficients: [1.15, 1.15, 1.10, 1.00, 0.90, 0.85],
    threshold_90: 0.85,
    threshold_100: 0.90,
    dm_mode: 'exclusive',
    other_mode: 'stack',
    cp_subsidy: 60000,
    sales_subsidy: 800
};

// 岗位配置
const ROLE_CONFIG = {
    CP: { name: '常委', rate: 0, hasRegion: true, hasNational: true, hasSubsidy: true },
    DM: { name: '总经理', rate: 0.004, hasRegion: true, hasNational: false, hasSubsidy: false },
    VP: { name: '副总经理', rate: 0.004, hasRegion: false, hasNational: false, hasSubsidy: false },
    MGR: { name: '部门经理', rate: 0.01, hasRegion: false, hasNational: false, hasSubsidy: false },
    SALES_USER: { name: '销售-用户部', rate: 0.02, hasRegion: false, hasNational: false, hasSubsidy: false },
    SALES_NEW: { name: '销售-新购', rate: 0.03, hasRegion: false, hasNational: false, hasSubsidy: true },
    SALES_EDU: { name: '销售-高校', rate: 0.03, hasRegion: false, hasNational: false, hasSubsidy: true }
};

// ============ 初始化 ============
document.addEventListener('DOMContentLoaded', () => {
    bindEvents();
    loadData();
});

async function loadData() {
    try {
        updateConnectionStatus('loading');
        
        // 加载参数
        const paramsResult = await api.getParams();
        if (paramsResult.status === 'success') {
            params = paramsResult.data;
            syncParamsToUI();
        }
        
        // 加载人员
        const personsResult = await api.getPersons();
        if (personsResult.status === 'success') {
            persons = personsResult.data;
        }
        
        updateConnectionStatus('online');
        calculate();
    } catch (error) {
        console.error('加载数据失败:', error);
        updateConnectionStatus('offline');
        showToast('数据加载失败: ' + error.message, 'error');
    }
}

function updateConnectionStatus(status) {
    const dot = document.getElementById('status-dot');
    const text = document.getElementById('status-text');
    
    switch (status) {
        case 'online':
            dot.className = 'status-dot';
            text.textContent = '已连接';
            break;
        case 'offline':
            dot.className = 'status-dot offline';
            text.textContent = '连接失败';
            break;
        case 'loading':
            dot.className = 'status-dot';
            text.textContent = '连接中...';
            break;
    }
}

function showToast(message, type = 'success') {
    const toast = document.getElementById('toast');
    toast.textContent = message;
    toast.className = `toast ${type} show`;
    setTimeout(() => {
        toast.classList.remove('show');
    }, 3000);
}

function syncParamsToUI() {
    for (let i = 1; i <= 6; i++) {
        document.getElementById(`coeff-${i}`).value = params.coefficients[i-1];
    }
    document.getElementById('threshold-90').value = params.threshold_90;
    document.getElementById('threshold-100').value = params.threshold_100;
    document.getElementById('cp-subsidy').value = params.cp_subsidy;
    document.getElementById('sales-subsidy').value = params.sales_subsidy;
    
    document.querySelectorAll('.switch-btn').forEach(btn => {
        const param = btn.dataset.param;
        const value = btn.dataset.value;
        if (param === 'dm-mode') {
            btn.classList.toggle('active', value === params.dm_mode);
        } else if (param === 'other-mode') {
            btn.classList.toggle('active', value === params.other_mode);
        }
    });
}

// ============ 事件绑定 ============
function bindEvents() {
    // 标签页切换
    document.querySelectorAll('.tab').forEach(tab => {
        tab.addEventListener('click', () => {
            document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
            document.querySelectorAll('.panel').forEach(p => p.classList.remove('active'));
            tab.classList.add('active');
            document.getElementById(`panel-${tab.dataset.tab}`).classList.add('active');
        });
    });
    
    // 参数输入变化
    document.querySelectorAll('.param-input').forEach(input => {
        input.addEventListener('change', () => {
            syncParamsFromUI();
            saveParams();
        });
    });
    
    // 叠加模式切换
    document.querySelectorAll('.switch-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            const param = btn.dataset.param;
            const value = btn.dataset.value;
            btn.parentElement.querySelectorAll('.switch-btn').forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            if (param === 'dm-mode') params.dm_mode = value;
            if (param === 'other-mode') params.other_mode = value;
            saveParams();
        });
    });
}

async function syncParamsFromUI() {
    for (let i = 1; i <= 6; i++) {
        params.coefficients[i-1] = parseFloat(document.getElementById(`coeff-${i}`).value) || 0;
    }
    params.threshold_90 = parseFloat(document.getElementById('threshold-90').value) || 0;
    params.threshold_100 = parseFloat(document.getElementById('threshold-100').value) || 0;
    params.cp_subsidy = parseFloat(document.getElementById('cp-subsidy').value) || 0;
    params.sales_subsidy = parseFloat(document.getElementById('sales-subsidy').value) || 0;
}

async function saveParams() {
    try {
        await api.updateParams(params);
        calculate();
    } catch (error) {
        console.error('保存参数失败:', error);
        showToast('保存参数失败: ' + error.message, 'error');
    }
}

// ============ 计算逻辑 ============
function calculate() {
    const results = persons.map(p => calculatePerson(p));
    renderResults(results);
    renderPersonList();
}

function calculatePerson(person) {
    const role = person.role;
    const config = ROLE_CONFIG[role];
    const result = {
        ...person,
        roleName: config.name,
        incentive: 0,
        completionBonus90: 0,
        completionBonus100: 0,
        completionBonusTotal: 0,
        regionBonus: 0,
        nationalBonus: 0,
        subsidy: 0,
        ceoBonus: person.ceo_bonus || 0,
        total: 0,
        completionRate: 0
    };
    
    // 产值合计
    const totalRev = (person.revenue || []).reduce((a, b) => a + (b || 0), 0);
    result.totalRevenue = totalRev;
    
    // 分公司完成率
    const companyRev = person.company_revenue || totalRev;
    const target = person.target || 0;
    result.completionRate = target > 0 ? companyRev / target : 0;
    
    // 过程激励
    if (config.rate > 0) {
        result.incentive = (person.revenue || []).reduce((sum, rev, i) => {
            return sum + (rev || 0) * config.rate * params.coefficients[i];
        }, 0);
    }
    
    // 完成奖
    if (role !== 'CP') {
        const collectionRate = person.collection_rate || 0;
        const ratio = person.ratio || 1;
        
        // 90%档
        if (result.completionRate >= 0.9 && collectionRate >= params.threshold_90) {
            if (role === 'DM') {
                result.completionBonus90 = Math.min(companyRev * 0.004, 40000);
            } else {
                result.completionBonus90 = companyRev * 0.015 * ratio;
            }
        }
        
        // 100%档
        if (result.completionRate >= 1.0 && collectionRate >= params.threshold_100) {
            if (role === 'DM') {
                result.completionBonus100 = Math.min(companyRev * 0.004, 40000);
            } else {
                result.completionBonus100 = companyRev * 0.015 * ratio;
            }
        }
        
        // 叠加模式
        const mode = role === 'DM' ? params.dm_mode : params.other_mode;
        if (mode === 'exclusive') {
            result.completionBonusTotal = Math.max(result.completionBonus90, result.completionBonus100);
        } else {
            result.completionBonusTotal = result.completionBonus90 + result.completionBonus100;
        }
    }
    
    // 区域奖
    if (config.hasRegion) {
        if (role === 'CP') {
            if (person.region_90) result.regionBonus += 30000;
            if (person.region_100) result.regionBonus += 30000;
        } else if (role === 'DM') {
            if (person.region_90 || person.region_100) result.regionBonus = 40000;
        }
    }
    
    // 全国奖
    if (config.hasNational && role === 'CP') {
        if (person.national_90) result.nationalBonus += 40000;
        if (person.national_100) result.nationalBonus += 40000;
    }
    
    // 固定补贴
    if (role === 'CP') {
        result.subsidy = params.cp_subsidy;
    } else if (role === 'SALES_NEW' || role === 'SALES_EDU') {
        result.subsidy = params.sales_subsidy * 6;
    }
    
    // 总计
    result.total = result.incentive + result.completionBonusTotal + 
                  result.regionBonus + result.nationalBonus + 
                  result.subsidy + result.ceoBonus;
    
    return result;
}

// ============ 渲染 ============
function formatMoney(num) {
    return '¥' + Math.round(num || 0).toLocaleString();
}

function renderResults(results) {
    // 汇总数据
    let sumIncentive = 0, sumCompletion = 0, sumRegion = 0, sumOther = 0, sumTotal = 0;
    const roleSums = {};
    
    results.forEach(r => {
        sumIncentive += r.incentive;
        sumCompletion += r.completionBonusTotal;
        sumRegion += r.regionBonus + r.nationalBonus;
        sumOther += r.subsidy + r.ceoBonus;
        sumTotal += r.total;
        
        if (!roleSums[r.role]) {
            roleSums[r.role] = { count: 0, total: 0, name: r.roleName };
        }
        roleSums[r.role].count++;
        roleSums[r.role].total += r.total;
    });
    
    document.getElementById('total-bonus').textContent = formatMoney(sumTotal);
    document.getElementById('total-count').textContent = results.length;
    document.getElementById('sum-incentive').textContent = formatMoney(sumIncentive);
    document.getElementById('sum-completion').textContent = formatMoney(sumCompletion);
    document.getElementById('sum-region').textContent = formatMoney(sumRegion);
    document.getElementById('sum-other').textContent = formatMoney(sumOther);
    
    // 按岗位汇总
    const roleSummaryHtml = Object.entries(roleSums).map(([role, data]) => `
        <div class="bonus-item">
            <span class="bonus-item-label">${data.name} (${data.count}人)</span>
            <span class="bonus-item-value">${formatMoney(data.total)}</span>
        </div>
    `).join('');
    document.getElementById('role-summary').innerHTML = roleSummaryHtml || '<div style="color:#999;font-size:13px">暂无数据</div>';
    
    // 明细列表
    const resultListHtml = results.length ? results.map(r => `
        <div class="person-item">
            <div class="person-header">
                <div>
                    <span class="person-name">${r.name}</span>
                    <span class="person-role">${r.roleName}</span>
                </div>
                <div class="person-bonus">${formatMoney(r.total)}</div>
            </div>
            <div class="bonus-detail">
                <div class="bonus-item">
                    <span class="bonus-item-label">过程激励</span>
                    <span class="bonus-item-value">${formatMoney(r.incentive)}</span>
                </div>
                <div class="bonus-item">
                    <span class="bonus-item-label">完成奖</span>
                    <span class="bonus-item-value">${formatMoney(r.completionBonusTotal)}</span>
                </div>
                <div class="bonus-item">
                    <span class="bonus-item-label">区域奖</span>
                    <span class="bonus-item-value">${formatMoney(r.regionBonus)}</span>
                </div>
                <div class="bonus-item">
                    <span class="bonus-item-label">全国奖</span>
                    <span class="bonus-item-value">${formatMoney(r.nationalBonus)}</span>
                </div>
                <div class="bonus-item">
                    <span class="bonus-item-label">固定补贴</span>
                    <span class="bonus-item-value">${formatMoney(r.subsidy)}</span>
                </div>
                <div class="bonus-item">
                    <span class="bonus-item-label">CEO奖金</span>
                    <span class="bonus-item-value">${formatMoney(r.ceoBonus)}</span>
                </div>
                <div class="bonus-item">
                    <span class="bonus-item-label">完成率</span>
                    <span class="bonus-item-value">${(r.completionRate * 100).toFixed(1)}%</span>
                </div>
                <div class="bonus-item">
                    <span class="bonus-item-label">回款率</span>
                    <span class="bonus-item-value">${((r.collection_rate || 0) * 100).toFixed(1)}%</span>
                </div>
            </div>
        </div>
    `).join('') : '<div class="empty-state"><div class="empty-state-icon">📊</div><p>暂无数据，请先添加人员</p></div>';
    document.getElementById('result-list').innerHTML = resultListHtml;
}

function renderPersonList() {
    const emptyEl = document.getElementById('empty-persons');
    const listEl = document.getElementById('person-list');
    
    if (persons.length === 0) {
        emptyEl.style.display = 'block';
        listEl.innerHTML = '';
        return;
    }
    
    emptyEl.style.display = 'none';
    listEl.innerHTML = persons.map((p, i) => `
        <div class="card">
            <div style="display:flex;justify-content:space-between;align-items:center">
                <div>
                    <strong>${p.name}</strong>
                    <span class="person-role" style="margin-left:8px">${ROLE_CONFIG[p.role].name}</span>
                </div>
                <div>
                    <button class="btn btn-sm btn-outline" onclick="editPerson(${p.id})">编辑</button>
                    <button class="delete-btn" onclick="deletePerson(${p.id})">🗑️</button>
                </div>
            </div>
            <div style="margin-top:12px;font-size:13px;color:var(--text-secondary)">
                ${p.region} · ${p.org || '-'} · 产值合计: ${formatMoney((p.revenue||[]).reduce((a,b)=>a+(b||0),0))}
            </div>
        </div>
    `).join('');
}

// ============ 模态框操作 ============
function showAddModal() {
    document.getElementById('modal-title').textContent = '添加人员';
    document.getElementById('edit-id').value = '';
    clearForm();
    document.getElementById('person-modal').classList.add('active');
}

function editPerson(id) {
    const p = persons.find(person => person.id === id);
    if (!p) return;
    
    document.getElementById('modal-title').textContent = '编辑人员';
    document.getElementById('edit-id').value = id;
    
    document.getElementById('input-name').value = p.name || '';
    document.getElementById('input-role').value = p.role || 'DM';
    document.getElementById('input-region').value = p.region || '华北';
    document.getElementById('input-org').value = p.org || '';
    
    for (let i = 1; i <= 6; i++) {
        document.getElementById(`input-rev-${i}`).value = (p.revenue && p.revenue[i-1]) || 0;
    }
    
    document.getElementById('input-company-rev').value = p.company_revenue || 0;
    document.getElementById('input-target').value = p.target || 0;
    document.getElementById('input-collection').value = p.collection_rate || 0.9;
    document.getElementById('input-ratio').value = p.ratio || '';
    document.getElementById('input-region-90').value = p.region_90 ? '1' : '0';
    document.getElementById('input-region-100').value = p.region_100 ? '1' : '0';
    document.getElementById('input-national-90').value = p.national_90 ? '1' : '0';
    document.getElementById('input-national-100').value = p.national_100 ? '1' : '0';
    document.getElementById('input-ceo-bonus').value = p.ceo_bonus || 0;
    
    document.getElementById('person-modal').classList.add('active');
}

function closeModal() {
    document.getElementById('person-modal').classList.remove('active');
}

function clearForm() {
    document.getElementById('input-name').value = '';
    document.getElementById('input-role').value = 'DM';
    document.getElementById('input-region').value = '华北';
    document.getElementById('input-org').value = '';
    for (let i = 1; i <= 6; i++) {
        document.getElementById(`input-rev-${i}`).value = 0;
    }
    document.getElementById('input-company-rev').value = 0;
    document.getElementById('input-target').value = 0;
    document.getElementById('input-collection').value = 0.9;
    document.getElementById('input-ratio').value = '';
    document.getElementById('input-region-90').value = '0';
    document.getElementById('input-region-100').value = '0';
    document.getElementById('input-national-90').value = '0';
    document.getElementById('input-national-100').value = '0';
    document.getElementById('input-ceo-bonus').value = 0;
}

async function savePerson() {
    const name = document.getElementById('input-name').value.trim();
    if (!name) {
        showToast('请输入姓名', 'error');
        return;
    }
    
    const person = {
        name: name,
        role: document.getElementById('input-role').value,
        region: document.getElementById('input-region').value,
        org: document.getElementById('input-org').value,
        revenue: [],
        company_revenue: parseFloat(document.getElementById('input-company-rev').value) || 0,
        target: parseFloat(document.getElementById('input-target').value) || 0,
        collection_rate: parseFloat(document.getElementById('input-collection').value) || 0,
        ratio: parseFloat(document.getElementById('input-ratio').value) || null,
        region_90: document.getElementById('input-region-90').value === '1',
        region_100: document.getElementById('input-region-100').value === '1',
        national_90: document.getElementById('input-national-90').value === '1',
        national_100: document.getElementById('input-national-100').value === '1',
        ceo_bonus: parseFloat(document.getElementById('input-ceo-bonus').value) || 0
    };
    
    for (let i = 1; i <= 6; i++) {
        person.revenue.push(parseFloat(document.getElementById(`input-rev-${i}`).value) || 0);
    }
    
    try {
        const editId = document.getElementById('edit-id').value;
        if (editId) {
            await api.updatePerson(parseInt(editId), person);
            showToast('人员信息已更新');
        } else {
            await api.createPerson(person);
            showToast('人员已添加');
        }
        
        closeModal();
        await loadData();
    } catch (error) {
        console.error('保存人员失败:', error);
        showToast('保存失败: ' + error.message, 'error');
    }
}

async function deletePerson(id) {
    if (!confirm('确定删除该人员吗？')) return;
    
    try {
        await api.deletePerson(id);
        showToast('人员已删除');
        await loadData();
    } catch (error) {
        console.error('删除人员失败:', error);
        showToast('删除失败: ' + error.message, 'error');
    }
}

// ============ 数据操作 ============
async function loadTestData() {
    if (persons.length > 0 && !confirm('将覆盖现有数据，确定加载测试数据？')) return;
    
    const testPersons = [
        { name: '王总', role: 'CP', region: '全国', org: '总部', revenue: [0,0,0,0,0,0], company_revenue: 0, target: 0, collection_rate: 0.95, ratio: null, region_90: true, region_100: true, national_90: true, national_100: false, ceo_bonus: 50000 },
        { name: '李总', role: 'DM', region: '华北', org: '北京分公司', revenue: [500000,600000,700000,800000,750000,650000], company_revenue: 4000000, target: 3800000, collection_rate: 0.92, ratio: null, region_90: true, region_100: false, national_90: false, national_100: false, ceo_bonus: 20000 },
        { name: '张经理', role: 'MGR', region: '华东', org: '上海分公司', revenue: [150000,180000,200000,220000,190000,160000], company_revenue: 3000000, target: 2800000, collection_rate: 0.91, ratio: 0.25, region_90: false, region_100: false, national_90: false, national_100: false, ceo_bonus: 5000 },
        { name: '陈销售', role: 'SALES_NEW', region: '华东', org: '上海分公司', revenue: [80000,90000,100000,110000,95000,85000], company_revenue: 3000000, target: 500000, collection_rate: 0.88, ratio: 0.15, region_90: false, region_100: false, national_90: false, national_100: false, ceo_bonus: 0 },
        { name: '刘副总', role: 'VP', region: '华南', org: '深圳分公司', revenue: [200000,250000,280000,300000,270000,230000], company_revenue: 2500000, target: 2300000, collection_rate: 0.93, ratio: 0.4, region_90: false, region_100: false, national_90: false, national_100: false, ceo_bonus: 10000 },
        { name: '赵销售', role: 'SALES_EDU', region: '西南', org: '成都分公司', revenue: [60000,70000,85000,90000,80000,65000], company_revenue: 1800000, target: 400000, collection_rate: 0.90, ratio: 0.2, region_90: false, region_100: false, national_90: false, national_100: false, ceo_bonus: 0 }
    ];
    
    try {
        for (const person of testPersons) {
            await api.createPerson(person);
        }
        showToast('测试数据已加载！');
        await loadData();
        // 切换到汇总页
        document.querySelector('.tab[data-tab="summary"]').click();
    } catch (error) {
        console.error('加载测试数据失败:', error);
        showToast('加载测试数据失败: ' + error.message, 'error');
    }
}

async function clearAllData() {
    if (!confirm('确定清空所有数据吗？此操作不可恢复！')) return;
    
    try {
        for (const person of persons) {
            await api.deletePerson(person.id);
        }
        showToast('所有数据已清空');
        await loadData();
    } catch (error) {
        console.error('清空数据失败:', error);
        showToast('清空数据失败: ' + error.message, 'error');
    }
}

async function migrateFromLocalStorage() {
    const localPersons = localStorage.getItem('bonus_persons');
    const localParams = localStorage.getItem('bonus_params');
    
    if (!localPersons && !localParams) {
        showToast('未找到浏览器本地数据', 'error');
        return;
    }
    
    if (!confirm('确定导入浏览器本地数据吗？将会覆盖现有数据！')) return;
    
    try {
        // 导入参数
        if (localParams) {
            const parsedParams = JSON.parse(localParams);
            // 转换格式
            const convertedParams = {
                coefficients: parsedParams.coefficients || [1.15, 1.15, 1.10, 1.00, 0.90, 0.85],
                threshold_90: parsedParams.threshold90 || 0.85,
                threshold_100: parsedParams.threshold100 || 0.90,
                dm_mode: parsedParams.dmMode || 'exclusive',
                other_mode: parsedParams.otherMode || 'stack',
                cp_subsidy: parsedParams.cpSubsidy || 60000,
                sales_subsidy: parsedParams.salesSubsidy || 800
            };
            await api.updateParams(convertedParams);
        }
        
        // 导入人员
        if (localPersons) {
            const parsedPersons = JSON.parse(localPersons);
            // 清空现有数据
            for (const person of persons) {
                await api.deletePerson(person.id);
            }
            
            // 添加本地数据
            for (const person of parsedPersons) {
                // 转换字段格式
                const convertedPerson = {
                    name: person.name,
                    role: person.role,
                    region: person.region,
                    org: person.org,
                    revenue: person.revenue || [],
                    company_revenue: person.companyRevenue || 0,
                    target: person.target || 0,
                    collection_rate: person.collectionRate || 0.9,
                    ratio: person.ratio,
                    region_90: person.region90 || false,
                    region_100: person.region100 || false,
                    national_90: person.national90 || false,
                    national_100: person.national100 || false,
                    ceo_bonus: person.ceoBonus || 0
                };
                await api.createPerson(convertedPerson);
            }
        }
        
        showToast(`成功导入本地数据！`);
        await loadData();
        
        // 切换到汇总页
        document.querySelector('.tab[data-tab="summary"]').click();
    } catch (error) {
        console.error('导入数据失败:', error);
        showToast('导入失败: ' + error.message, 'error');
    }
}
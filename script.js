// timetable_data.js で定義された timetableData 変数を使用
// const timetableData = [ ... ]; の形式でデータが格納されていると想定

let allTimetableData = []; // 整形済み時間割データ本体の全データ
let classNames = [];       // クラス選択プルダウン用のクラス名リスト

// ページロード時の初期処理
document.addEventListener('DOMContentLoaded', () => {
    // timetableData が定義されていることを確認
    if (typeof timetableData !== 'undefined' && Array.isArray(timetableData)) {
        allTimetableData = timetableData;
        
        // 曜日と時限をソート可能な形に変換・整形
        const weekdaysOrder = ['月', '火', '水', '木', '金']; // ★修正：土日を除外
        allTimetableData = allTimetableData.map(row => ({
            ...row,
            時限: parseInt(row['時限']), // 時限を数値に変換
            曜日Index: weekdaysOrder.indexOf(row['曜日']) // 曜日を数値インデックスに変換
        })).filter(row => row.曜日Index !== -1) // ★修正：有効な曜日（月～金）のみにフィルタリング
          .sort((a, b) => {
            // クラス -> 曜日 -> 時限 の順でソート
            if (a['クラス'] !== b['クラス']) {
                return String(a['クラス']).localeCompare(String(b['クラス']));
            }
            if (a.曜日Index !== b.曜日Index) {
                return a.曜日Index - b.曜日Index;
            }
            return a.時限 - b.時限; 
        });

        // クラス名のリストを生成
        classNames = [...new Set(allTimetableData.map(row => row['クラス']))].sort();

        populateClassSelect(); // クラス選択プルダウンを生成
        setupEventListeners(); // ★修正：ドロップダウン生成後にイベントリスナーを設定
        
        // 初期表示クラスを決定
        const urlParams = new URLSearchParams(window.location.search);
        const initialClassFromUrl = urlParams.get('class'); // URLから 'class' パラメータを取得
        
        let classToDisplay = null;

        if (initialClassFromUrl && classNames.includes(initialClassFromUrl)) {
            // URLパラメータで指定されたクラスが存在する場合、それを表示
            classToDisplay = initialClassFromUrl;
        } else {
            // URLパラメータが指定されていないか、無効な場合、
            // 「2年1組」をデフォルトとして設定
            if (classNames.includes('2年1組')) { // ★修正：初期表示を「2年1組」に
                classToDisplay = '2年1組';
            } else if (classNames.length > 0) {
                // 「2年1組」が存在しない場合、クラス一覧の最初のクラスをデフォルトにする
                classToDisplay = classNames[0];
            }
        }

        // 実際にプルダウンの選択状態を更新し、時間割を表示
        if (classToDisplay) {
            document.getElementById('class-select').value = classToDisplay;
            displayClassTimetable(classToDisplay);
        } else {
            document.getElementById('timetable-display').innerHTML = '<p class="info-message">表示可能なクラスが見つかりませんでした。データファイルを確認してください。</p>';
        }

    } else {
        console.error('timetableData が見つからないか、不正な形式です。');
        document.getElementById('timetable-display').innerHTML = '<p class="error-message">時間割データの読み込みに失敗しました。</p>';
    }
});


// クラス選択プルダウンの生成
function populateClassSelect() {
    const select = document.getElementById('class-select');
    select.innerHTML = ''; // 既存のオプションをクリア

    classNames.forEach(cls => {
        const option = document.createElement('option');
        option.value = cls;
        option.textContent = cls;
        select.appendChild(option);
    });
}

// イベントリスナーの設定
function setupEventListeners() {
    // 表示ボタンは削除したので、ドロップダウンの変更イベントをリッスン
    document.getElementById('class-select').addEventListener('change', (event) => {
        const selectedClass = event.target.value;
        displayClassTimetable(selectedClass);
    });
}

// クラス時間割表の表示ロジック
function displayClassTimetable(className) {
    const displayDiv = document.getElementById('timetable-display');
    displayDiv.innerHTML = ''; // 表示領域をクリア

    if (!className) {
        displayDiv.innerHTML = '<p class="info-message">表示するクラスを選択してください。</p>';
        return;
    }

    const filteredData = allTimetableData.filter(row => row['クラス'] === className);

    if (filteredData.length === 0) {
        displayDiv.innerHTML = `<p class="info-message">${className} の時間割データが見つかりませんでした。</p>`;
        return;
    }

    // ★曜日のリストを月～金に限定
    const weekdays = ['月', '火', '水', '木', '金']; 
    // 全ての時限を取得し、ソート (整形済みデータから取得)
    const allPeriods = [...new Set(allTimetableData.map(row => parseInt(row['時限'])).filter(n => !isNaN(n)))].sort((a, b) => a - b);

    // 時間割表のタイトルを追加
    const titleElement = document.createElement('h2');
    titleElement.textContent = `${className} 時間割`;
    displayDiv.appendChild(titleElement);

    const table = document.createElement('table');
    table.classList.add('timetable-table');

    // ヘッダー行 (時限 + 曜日)
    const thead = table.createTHead();
    const headerRow = thead.insertRow();
    headerRow.insertCell().textContent = '時限'; // 左上の空セル
    weekdays.forEach(day => {
        const th = document.createElement('th');
        th.textContent = day;
        headerRow.appendChild(th);
    });

    // データ行
    const tbody = table.createTBody();
    allPeriods.forEach(period => {
        const row = tbody.insertRow();
        row.insertCell().textContent = period; // 時限セル

        weekdays.forEach(day => {
            const cell = row.insertCell();
            // 該当する授業データを見つける
            const lesson = filteredData.find(d => d['曜日'] === day && parseInt(d['時限']) === period);
            
            if (lesson) {
                const lessonInfoDiv = document.createElement('div');
                lessonInfoDiv.classList.add('lesson-info');
                
                // ★科目名のみをシンプルに表示
                const subjectSpan = document.createElement('span');
                subjectSpan.classList.add('subject');
                subjectSpan.textContent = lesson['科目'];
                lessonInfoDiv.appendChild(subjectSpan);
                
                cell.appendChild(lessonInfoDiv);
            } else {
                cell.textContent = '-'; // 授業がない場合
            }
        });
    });
    
    displayDiv.appendChild(table);
}
from win11toast import *
import tkinter as tk
import sqlite3
import datetime

class LabelManagerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("日課管理ツール")
        self.root.geometry("600x600")
        
        # データベースの初期化
        self.init_db()
        
        # 日付チェックのリセット処理
        self.reset_checks_based_on_date()

        # ラベルを表示するフレーム
        self.label_frame = tk.Frame(self.root)
        self.label_frame.pack(pady=10)

        # ラベル追加用のエントリとリセットタイプの選択
        self.entry = tk.Entry(self.root)
        self.entry.pack(pady=5)

        self.reset_type = tk.StringVar(value="day")
        reset_options = [("日ごと", "day"), ("月曜ごと", "week"), ("月ごと", "month")]
        for text, value in reset_options:
            tk.Radiobutton(self.root, text=text, variable=self.reset_type, value=value).pack()

        # ラベル追加、削除ボタン
        self.add_button = tk.Button(self.root, text="追加", command=self.add_label)
        self.add_button.pack(pady=5)

        self.delete_button = tk.Button(self.root, text="削除", command=self.delete_label)
        self.delete_button.pack(pady=5)

        # 初回起動時にラベルを読み込んで表示
        self.refresh_labels()

    def init_db(self):
        """データベースを初期化する"""
        conn = sqlite3.connect('labels.db')
        cursor = conn.cursor()
        # テーブルの作成またはチェック
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS labels (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                text TEXT NOT NULL,
                checked INTEGER DEFAULT 0,
                last_modified DATE
            )
        ''')

        # `reset_type` カラムが存在しない場合に追加する
        try:
            cursor.execute('ALTER TABLE labels ADD COLUMN reset_type TEXT DEFAULT "day"')
        except sqlite3.OperationalError:
            # カラムが既に存在する場合、エラーを無視
            pass

        # `last_modified` カラムが存在しない場合に追加する
        try:
            cursor.execute('ALTER TABLE labels ADD COLUMN last_modified DATE')
        except sqlite3.OperationalError:
            # カラムが既に存在する場合、エラーを無視
            pass

        conn.commit()
        conn.close()

    def load_labels(self):
        """データベースからラベルとそのチェック状態を取得する"""
        conn = sqlite3.connect('labels.db')
        cursor = conn.cursor()
        cursor.execute('SELECT id, text, checked, reset_type FROM labels')
        labels = cursor.fetchall()
        conn.close()
        return labels

    def refresh_labels(self):
        """ラベルフレームをリフレッシュして、リセットタイプごとにラベルを再描画する"""
        for widget in self.label_frame.winfo_children():
            widget.destroy()

        labels = self.load_labels()
        sections = {"day": "日ごと", "week": "月曜ごと", "month": "月ごと"}

        for section, section_name in sections.items():
            tk.Label(self.label_frame, text=f"=== {section_name} ===", font=("Helvetica", 14, "bold")).pack()
            for label in labels:
                label_id, text, checked, reset_type = label
                if reset_type == section:
                    var = tk.IntVar(value=checked)
                    cb = tk.Checkbutton(self.label_frame, text=text, variable=var, command=lambda v=var, i=label_id: self.update_check_status(i, v))
                    cb.pack()

    def update_check_status(self, label_id, var):
        """チェックボックスの状態をデータベースに更新"""
        checked = var.get()
        conn = sqlite3.connect('labels.db')
        cursor = conn.cursor()
        cursor.execute('UPDATE labels SET checked = ?, last_modified = ? WHERE id = ?', (checked, datetime.date.today(), label_id))
        conn.commit()
        conn.close()

    def add_label_to_db(self, text, reset_type):
        """ラベルをデータベースに追加する"""
        conn = sqlite3.connect('labels.db')
        cursor = conn.cursor()
        cursor.execute('INSERT INTO labels (text, checked, reset_type, last_modified) VALUES (?, 0, ?, ?)', (text, reset_type, datetime.date.today()))
        conn.commit()
        conn.close()

    def add_label(self):
        """エントリから入力されたラベルを追加"""
        label_text = self.entry.get()
        reset_type = self.reset_type.get()
        if label_text:
            self.add_label_to_db(label_text, reset_type)
            self.entry.delete(0, tk.END)
            self.refresh_labels()

    def delete_label_from_db(self, text):
        """指定されたラベルをデータベースから削除"""
        conn = sqlite3.connect('labels.db')
        cursor = conn.cursor()
        cursor.execute('DELETE FROM labels WHERE text = ?', (text,))
        conn.commit()
        conn.close()

    def delete_label(self):
        """エントリから入力されたラベルを削除"""
        label_text = self.entry.get()
        if label_text:
            self.delete_label_from_db(label_text)
            self.entry.delete(0, tk.END)
            self.refresh_labels()

    def reset_checks_based_on_date(self):
        """日付、曜日、月に基づいてチェック状態をリセット"""
        today = datetime.date.today()
        conn = sqlite3.connect('labels.db')
        cursor = conn.cursor()
        cursor.execute('SELECT id, last_modified, reset_type FROM labels')
        labels = cursor.fetchall()

        for label in labels:
            label_id, last_modified, reset_type = label
            if last_modified:
                last_date = datetime.datetime.strptime(last_modified, '%Y-%m-%d').date()

                # 日ごとにリセット
                if reset_type == "day" and today != last_date:
                    cursor.execute('UPDATE labels SET checked = 0 WHERE id = ?', (label_id,))
                
                # 月曜後リセット
                if reset_type == "week" and today.weekday() == 0 and last_date.weekday() != 0:
                    cursor.execute('UPDATE labels SET checked = 0 WHERE id = ?', (label_id,))

                # 月ごとリセット
                if reset_type == "month" and today.month != last_date.month:
                    cursor.execute('UPDATE labels SET checked = 0 WHERE id = ?', (label_id,))

        conn.commit()
        conn.close()
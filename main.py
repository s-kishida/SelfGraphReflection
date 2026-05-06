import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import japanize_matplotlib
import io
import json
import numpy as np
from matplotlib.ticker import MultipleLocator

# --- デザイン：以前のカスタムCSSをStreamlitに注入 ---
def local_css():
    st.markdown("""
        <style>
        /* 全体の背景色（Pure White） */
        .stApp {
            background-color: #FAFAFA;
            color: #111827; /* より濃い黒 */
        }
        /* サイドバー全体の背景とテキスト色 */
        [data-testid="stSidebar"], [data-testid="stSidebar"] .stMarkdown p {
            background-color: #DCEAF7;
            color: #111827 !important;
        }
        /* セクション見出し（FOREST） */
        h1, h2, h3, h4, h5, h6, [data-testid="stSidebar"] h2 {
            color: #2E5B4E !important;
            font-weight: 700 !important;
        }
        /* 全ての入力系ウィジェットの背景を白、文字を黒に強制 */
        .stTextInput input, 
        .stSelectbox div[data-baseweb="select"] > div,
        .stMultiSelect div[data-baseweb="select"] > div,
        .stNumberInput input,
        .stTextArea textarea {
            background-color: #FFFFFF !important;
            color: #111827 !important;
            border: 1px solid #D1D5DB !important;
        }
        /* Number Input の +/- ボタンや背景 */
        .stNumberInput div[data-baseweb="input"] {
            background-color: #FFFFFF !important;
        }
        /* エキスパンダーのタイトルと背景 */
        .stExpander {
            background-color: #FFFFFF !important;
            border: 1px solid #E5E7EB !important;
        }
        .stExpander details summary {
            color: #111827 !important;
            font-weight: 600;
        }
        /* チェックボックスのラベル色 */
        .stCheckbox label {
            color: #111827 !important;
        }
        /* マルチセレクトの選択済みタグ */
        span[data-baseweb="tag"] {
            background-color: #2E5B4E !important;
            color: #FFFFFF !important;
        }
        /* ボタンのデザイン（反転：白背景に緑枠） */
        .stButton>button, .stDownloadButton>button {
            background-color: #FFFFFF !important;
            color: #2E5B4E !important;
            border: 2px solid #2E5B4E !important;
            border-radius: 8px !important;
            font-weight: 700;
            width: 100%;
        }
        .stButton>button:hover, .stDownloadButton>button:hover {
            background-color: #2E5B4E !important;
            color: #FFFFFF !important;
        }
        /* キャプションや小さい文字 */
        .stCaption, caption {
            color: #4B5563 !important;
        }
        /* ファイルアップローダー */
        [data-testid="stFileUploader"] {
            background-color: #F3F4F6;
            border: 1px dashed #D1D5DB;
        }
        </style>
    """, unsafe_allow_html=True)

local_css()

# タイトル（以前のスタイル）
st.title("Self-Graph Reflection")
st.markdown("<p style='color: #374151; margin-top: -15px;'>高校生のためのグラフ作成ツール</p>", unsafe_allow_html=True)

# --- サイドバー：以前のセクション構成を再現 ---
with st.sidebar:
    st.header("Data Input")
    uploaded_file = st.file_uploader("CSVファイルを選択", type="csv")
    
    df = None
    if uploaded_file:
        try:
            try:
                df = pd.read_csv(uploaded_file)
            except UnicodeDecodeError:
                uploaded_file.seek(0)
                df = pd.read_csv(uploaded_file, encoding='shift-jis')
        except Exception as e:
            st.error(f"Error: {e}")

    if df is not None:
        st.divider()
        st.header("Axis Settings")
        chart_type = st.selectbox("Chart Type (グラフの種類)", [
            "折れ線グラフ", "散布図", "棒グラフ", "複合グラフ", "ヒストグラム", "円グラフ", "箱ひげ図", "バイオリンプロット"
        ])
        
        # グラフの種類に応じて設定項目を変える
        if chart_type in ["折れ線グラフ", "散布図", "棒グラフ", "複合グラフ"]:
            x_axis = st.selectbox("X-Axis (横軸)", df.columns)
            
            # 数値列を優先的にリストアップ
            numeric_cols = [c for c in df.columns if pd.api.types.is_numeric_dtype(df[c]) and c != x_axis]
            other_cols = [c for c in df.columns if not pd.api.types.is_numeric_dtype(df[c]) and c != x_axis]
            selectable_y = numeric_cols + other_cols
            
            y_axes = st.multiselect("Y-Axis (縦軸: 複数選択可)", selectable_y, default=[numeric_cols[0]] if numeric_cols else [])
            
            # デフォルト配色（イメージのパレットに基づいた配色）
            default_colors = ["#2E5B4E", "#A7C1B2", "#F2C94C", "#4B5563", "#768B7E", "#E09E8F", "#8FA2E0", "#E0C38F"]
            
            y_configs = {}
            if y_axes:
                with st.expander("Series Settings (個別の設定)", expanded=True):
                    for i, col in enumerate(y_axes):
                        st.write(f"**{col}**")
                        c_typ, c_col, c_siz, c_leg = st.columns([2, 1, 1, 1])
                        
                        # プロットの種類
                        if chart_type == "複合グラフ":
                            p_type = c_typ.selectbox("Type", ["Line", "Scatter", "Bar"], key=f"type_{col}")
                        else:
                            p_type = "Line" if chart_type == "折れ線グラフ" else ("Scatter" if chart_type == "散布図" else "Bar")
                        
                        # 色
                        p_color = c_col.color_picker("Color", default_colors[i % len(default_colors)], key=f"color_{col}")
                        
                        # サイズ
                        if p_type == "Bar":
                            p_size = c_siz.number_input("Width Scale", 0.1, 2.0, 1.0, step=0.1, format="%g", key=f"size_{col}")
                        else:
                            p_size = c_siz.number_input("Size", 1.0, 50.0, 8.0 if p_type == "Scatter" else 3.0, step=1.0, format="%g", key=f"size_{col}")
                        
                        # 凡例表示
                        p_leg = c_leg.checkbox("Legend", value=True, key=f"leg_{col}")
                        
                        y_configs[col] = {"type": p_type, "color": p_color, "size": p_size, "show_legend": p_leg}

            y_axis_mapping = {}
            axis_configs = {0: {"name": y_axes[0] if y_axes else "", "unit": "", "min": None, "max": None, "label_size": 18, "tick_size": 14}}
            
            if y_axes and chart_type != "円グラフ":
                with st.expander("Axis Allocation & Settings (軸の設定)", expanded=False):
                    active_ids = {0}
                    for col in y_axes:
                        y_axis_mapping[col] = st.number_input(f"Axis for {col} (0:左, 1:右, 2+:右オフセット)", 0, 5, 0, key=f"axis_{col}")
                        active_ids.add(y_axis_mapping[col])
                    
                    st.divider()
                    for idx in sorted(list(active_ids)):
                        st.write(f"**Axis {idx} Config**")
                        c_n, c_u = st.columns(2)
                        a_name = c_n.text_input(f"Name", value=y_axes[0] if idx==0 and y_axes else "", key=f"aname_{idx}")
                        a_unit = c_u.text_input(f"Unit", key=f"aunit_{idx}")
                        
                        c_mi, c_ma = st.columns(2)
                        a_min = c_mi.number_input(f"Min", value=None, step=1.0, format="%g", key=f"amin_{idx}")
                        a_max = c_ma.number_input(f"Max", value=None, step=1.0, format="%g", key=f"amax_{idx}")
                        
                        c_fl, c_ft = st.columns(2)
                        a_font_l = c_fl.number_input(f"Label Size", 10, 40, 18, step=1, key=f"afont_l_{idx}")
                        a_font_t = c_ft.number_input(f"Tick Size", 8, 30, 14, step=1, key=f"afont_t_{idx}")
                        
                        axis_configs[idx] = {"name": a_name, "unit": a_unit, "min": a_min, "max": a_max, "label_size": a_font_l, "tick_size": a_font_t}
            else:
                for col in y_axes: y_axis_mapping[col] = 0
        elif chart_type == "円グラフ":
            x_axis = st.selectbox("Labels (ラベルにする列)", df.columns)
            
            numeric_cols = [c for c in df.columns if pd.api.types.is_numeric_dtype(df[c]) and c != x_axis]
            other_cols = [c for c in df.columns if not pd.api.types.is_numeric_dtype(df[c]) and c != x_axis]
            selectable_y = numeric_cols + other_cols
            
            y_axes = st.multiselect("Values (数値の列: 1つ選択)", selectable_y, default=[numeric_cols[0]] if numeric_cols else [], max_selections=1)
        elif chart_type == "ヒストグラム":
            x_axis = None
            y_axes = st.multiselect("Data (対象の列: 複数選択可)", df.columns, default=[df.columns[0]])
            hist_bins = st.number_input("Bins (階級数)", 1, 100, 20, step=1)
        else: # 箱ひげ図, バイオリンプロット
            x_axis = None
            y_axes = st.multiselect("Data (対象の列: 複数選択可)", df.columns, default=df.columns.tolist()[:3])
        

        st.divider()
        st.header("Label Settings")
        default_title = f"{chart_type}"
        if y_axes:
            if chart_type in ["折れ線グラフ", "散布図", "棒グラフ"] and x_axis:
                default_title = f"{', '.join(y_axes)} vs {x_axis}"
            else:
                default_title = f"{chart_type}: {', '.join(y_axes)}"
                
        chart_title = st.text_input("Graph Title", value=default_title)
        
        c1, c2 = st.columns(2)
        x_name = c1.text_input("X Name", value=x_axis if x_axis else "")
        x_unit = c2.text_input("X Unit", placeholder="s, m, etc.")
        
        
        st.subheader("Global Font Sizes")
        f1, f2, f3 = st.columns(3)
        font_title = f1.number_input("Title Size", 10, 50, 24, step=1)
        # Label/Tick sizes are now primarily handled per-axis in Axis Settings
        font_label_global = f2.number_input("Global Label Size", 10, 40, 18, step=1)
        font_tick_global = f3.number_input("Global Tick Size", 8, 30, 14, step=1)

        # Global settings are now handled per-series

        st.divider()
        st.header("Graph Size")
        s1, s2 = st.columns(2)
        width_val = s1.number_input("Width", 5.0, 30.0, 10.0, step=1.0, format="%g")
        height_val = s2.number_input("Height", 3.0, 30.0, 6.0, step=1.0, format="%g")
        
        aspect_choice = st.selectbox("Aspect Ratio (Data)", ["auto", "equal", "custom"], index=0)
        aspect_val = None
        if aspect_choice == "custom":
            aspect_val = st.number_input("Custom Ratio (Height/Width)", value=1.0, step=0.1, format="%g")
        elif aspect_choice == "equal":
            aspect_val = "equal"
        else:
            aspect_val = "auto"

        st.divider()
        st.header("Scale Settings")
        c_sc1, c_sc2 = st.columns(2)
        xmin_val = c_sc1.number_input("X Min (Auto if empty)", value=None, step=1.0, format="%g")
        xmax_val = c_sc2.number_input("X Max (Auto if empty)", value=None, step=1.0, format="%g")
        
        c_sc3, c_sc4 = st.columns(2)
        ymin_val = c_sc3.number_input("Y Min (Auto if empty)", value=None, step=1.0, format="%g")
        ymax_val = c_sc4.number_input("Y Max (Auto if empty)", value=None, step=1.0, format="%g")

        st.divider()
        st.header("Tick & Grid Details")
        with st.expander("X-Axis Ticks"):
            x_major_step = st.number_input("X Major Interval", value=None, step=1.0, format="%g", key="x_maj")
            x_minor_step = st.number_input("X Minor Interval", value=None, step=1.0, format="%g", key="x_min")
        with st.expander("Y-Axis Ticks"):
            y_major_step = st.number_input("Y Major Interval", value=None, step=1.0, format="%g", key="y_maj")
            y_minor_step = st.number_input("Y Minor Interval", value=None, step=1.0, format="%g", key="y_min")
        with st.expander("Grid & Other"):
            grid_major = st.checkbox("Show Major Grid", value=True)
            grid_minor = st.checkbox("Show Minor Grid", value=False)
            tick_dir = st.selectbox("Tick Direction (目盛の向き)", ["in", "out", "inout"], index=0)

# --- メインエリア ---
if df is not None:
    # データ情報の表示
    with st.expander("アップロードされたデータの詳細を確認", expanded=False):
        st.subheader("データ概要")
        # 各列の情報をまとめる
        info_df = pd.DataFrame({
            "列名": df.columns,
            "データ型": [str(t) for t in df.dtypes],
            "有効データ数": df.count().values,
            "欠損数": df.isnull().sum().values
        })
        st.table(info_df)
        
        st.subheader("データの数値参照")
        total_rows = len(df)
        if total_rows > 50:
            page_size = 50
            num_pages = (total_rows - 1) // page_size + 1
            
            # セッション状態でのページ管理
            if "page_num" not in st.session_state:
                st.session_state.page_num = 1
            
            # --- ページ番号と「次へ」の配置 ---
            cols_spec = [1] * num_pages + [2, 10]
            p_cols = st.columns(cols_spec)
            
            for i in range(1, num_pages + 1):
                with p_cols[i-1]:
                    st.markdown("<div class='page-num-row'>", unsafe_allow_html=True)
                    if i == st.session_state.page_num:
                        # 現在のページは強調表示
                        st.markdown(f"<div style='text-align:center; color:#2E5B4E; font-size:18px; font-weight:bold; margin-top:5px; border-bottom: 2px solid #2E5B4E;'>{i}</div>", unsafe_allow_html=True)
                    else:
                        if st.button(str(i), key=f"pg_{i}"):
                            st.session_state.page_num = i
                            st.rerun()
                    st.markdown("</div>", unsafe_allow_html=True)
            
            # 「次へ」ボタン
            with p_cols[num_pages]:
                st.markdown("<div class='page-num-row'>", unsafe_allow_html=True)
                if st.session_state.page_num < num_pages:
                    if st.button("次へ >", key="pg_next"):
                        st.session_state.page_num += 1
                        st.rerun()
                st.markdown("</div>", unsafe_allow_html=True)
                
            # 指定範囲のデータを表示
            page_num = st.session_state.page_num
            start_idx = (page_num - 1) * page_size
            end_idx = min(start_idx + page_size, total_rows)
            st.caption(f"{total_rows}行中 {start_idx + 1} 〜 {end_idx} 行目を表示しています")
            st.dataframe(df.iloc[start_idx:end_idx], use_container_width=True)
        else:
            st.dataframe(df, use_container_width=True)
    
    if not y_axes:
        st.info("👈 サイドバーで描画するデータを選択してください。")
    else:
        # グラフ作成
        fig, ax = plt.subplots(figsize=(width_val, height_val), facecolor='#FFFFFF')
        ax.set_facecolor('#FFFFFF')
        
        code_snippets = []
        
        # ラベル整形用関数
        def fmt(n, u):
            if n and u: return f"{n} ({u})"
            return n if n else (f"({u})" if u else "")
        
        # データの数値チェックと集計
        plot_df = df.copy()
        if y_axes and chart_type in ["折れ線グラフ", "散布図", "棒グラフ", "複合グラフ", "円グラフ"]:
            for col in y_axes:
                if not pd.api.types.is_numeric_dtype(df[col]):
                    st.warning(f"⚠️ '{col}' は数値データではないため、正しく表示されない可能性があります。数値の列を選択してください。")
            
            # カテゴリカルなX軸で重複がある場合、値を合計するオプション（自動適用）
            if x_axis and not pd.api.types.is_numeric_dtype(df[x_axis]):
                if df[x_axis].duplicated().any():
                    st.info(f"💡 '{x_axis}' に重複があるため、値を合計して表示します。")
                    plot_df = df.groupby(x_axis, sort=False)[y_axes].sum().reset_index()
        
        try:
            if chart_type in ["折れ線グラフ", "散布図", "棒グラフ", "複合グラフ"]:
                # X軸が数値かどうかを判定
                is_numeric_x = pd.api.types.is_numeric_dtype(plot_df[x_axis])
                
                # 軸の初期化
                axes = {0: ax}
                
                # 座標の決定
                if is_numeric_x and chart_type != "棒グラフ":
                    # 実数値ベース
                    x_plot = plot_df[x_axis].values
                    use_index_x = False
                else:
                    # カテゴリベース
                    x_plot = np.arange(len(plot_df))
                    use_index_x = True
                
                bar_cols = [c for c, conf in y_configs.items() if conf.get("type") == "Bar"]
                if bar_cols:
                    if not use_index_x and len(df) > 1:
                        # 数値軸の場合、データの最小間隔に合わせて棒の幅を計算
                        diffs = np.diff(np.sort(x_plot))
                        min_diff = np.min(diffs[diffs > 0]) if any(diffs > 0) else 1.0
                        total_width = min_diff * 0.8
                    else:
                        total_width = 0.8
                    width = total_width / len(bar_cols)
                
                max_axis_idx = max(y_axis_mapping.values()) if y_axis_mapping else 0
                for i in range(1, max_axis_idx+1):
                    new_ax = ax.twinx()
                    if i > 1:
                        new_ax.spines["right"].set_position(("axes", 1.0 + (i-1)*0.15))
                    axes[i] = new_ax
                    code_snippets.append(f"ax{i} = ax.twinx()")
                    if i > 1:
                        code_snippets.append(f"ax{i}.spines['right'].set_position(('axes', {1.0 + (i-1)*0.15}))")

                bar_count = 0
                for col in y_axes:
                    conf = y_configs[col]
                    p_type = conf["type"]
                    p_color = conf["color"]
                    p_size = conf["size"]
                    p_label = col if conf["show_legend"] else "_nolegend_"
                    
                    a_idx = y_axis_mapping.get(col, 0)
                    target_ax = axes[a_idx]
                    ax_prefix = f"ax{a_idx}" if a_idx > 0 else "ax"
                    
                    if p_type == "Line":
                        target_ax.plot(x_plot, plot_df[col], marker='o', color=p_color, linewidth=p_size, markersize=p_size*2, label=p_label)
                        code_snippets.append(f"{ax_prefix}.plot(x_plot, plot_df['{col}'], marker='o', color='{p_color}', linewidth={p_size}, markersize={p_size*2}, label='{p_label}')")
                    elif p_type == "Scatter":
                        target_ax.scatter(x_plot, plot_df[col], s=p_size*10, color=p_color, label=p_label, alpha=0.7)
                        code_snippets.append(f"{ax_prefix}.scatter(x_plot, plot_df['{col}'], s={p_size*10}, color='{p_color}', label='{p_label}', alpha=0.7)")
                    elif p_type == "Bar":
                        current_width = width * p_size
                        if len(bar_cols) > 0:
                            offset = (bar_count - len(bar_cols)/2 + 0.5) * width
                            target_ax.bar(x_plot + offset, plot_df[col], current_width, color=p_color, label=p_label)
                            code_snippets.append(f"{ax_prefix}.bar(x_plot + {offset}, plot_df['{col}'], {current_width}, color='{p_color}', label='{p_label}')")
                            bar_count += 1
                        else:
                            target_ax.bar(x_plot, plot_df[col], width=current_width, color=p_color, label=p_label)
                            code_snippets.append(f"{ax_prefix}.bar(x_plot, plot_df['{col}'], width={current_width}, color='{p_color}', label='{p_label}')")
                
                if use_index_x:
                    ax.set_xticks(x_plot)
                    ax.set_xticklabels(plot_df[x_axis])
                    code_snippets.insert(0, f"ax.set_xticks(x_plot)\nax.set_xticklabels(plot_df['{x_axis}'])")
                
                code_snippets.insert(0, f"import numpy as np\nx_plot = ... # values or arange\n")

                # 各軸の個別設定を適用
                for i, target_ax in axes.items():
                    conf = axis_configs.get(i, {})
                    a_name = conf.get("name", "")
                    a_unit = conf.get("unit", "")
                    a_min = conf.get("min")
                    a_max = conf.get("max")
                    a_label_fs = conf.get("label_size", font_label_global)
                    a_tick_fs = conf.get("tick_size", font_tick_global)
                    
                    target_ax.set_ylabel(fmt(a_name, a_unit), fontsize=a_label_fs, color='#1F2937')
                    target_ax.tick_params(axis='y', labelsize=a_tick_fs, colors='#1F2937')
                    
                    if a_min is not None: target_ax.set_ylim(bottom=a_min)
                    if a_max is not None: target_ax.set_ylim(top=a_max)
                    
                    ax_prefix = f"ax{i}" if i > 0 else "ax"
                    code_snippets.append(f"{ax_prefix}.set_ylabel('{fmt(a_name, a_unit)}', fontsize={a_label_fs})")
                    code_snippets.append(f"{ax_prefix}.tick_params(axis='y', labelsize={a_tick_fs})")
                    if a_min is not None: code_snippets.append(f"{ax_prefix}.set_ylim(bottom={a_min})")
                    if a_max is not None: code_snippets.append(f"{ax_prefix}.set_ylim(top={a_max})")

            elif chart_type == "ヒストグラム":
                axes = {0: ax}
                ax.hist([df[col].dropna() for col in y_axes], bins=hist_bins, label=y_axes, alpha=0.7)
                code_snippets.append(f"ax.hist([df[col].dropna() for col in {y_axes}], bins={hist_bins}, label={y_axes}, alpha=0.7)")
                
            elif chart_type == "円グラフ":
                axes = {0: ax}
                val_col = y_axes[0]
                ax.pie(plot_df[val_col], labels=plot_df[x_axis], autopct='%1.1f%%', startangle=90, counterclock=False)
                code_snippets.append(f"ax.pie(plot_df['{val_col}'], labels=plot_df['{x_axis}'], autopct='%1.1f%%', startangle=90, counterclock=False)")
                
            elif chart_type == "箱ひげ図":
                axes = {0: ax}
                ax.boxplot([df[col].dropna() for col in y_axes], labels=y_axes)
                code_snippets.append(f"ax.boxplot([df[col].dropna() for col in {y_axes}], labels={y_axes})")
                
            elif chart_type == "バイオリンプロット":
                axes = {0: ax}
                parts = ax.violinplot([df[col].dropna() for col in y_axes], showmeans=True)
                ax.set_xticks(range(1, len(y_axes) + 1))
                ax.set_xticklabels(y_axes)
                code_snippets.append(f"ax.violinplot([df[col].dropna() for col in {y_axes}], showmeans=True)")


            if chart_type != "円グラフ":
                ax.set_xlabel(fmt(x_name, x_unit) or (x_axis if x_axis else ""), fontsize=font_label_global, color='#1F2937')
            
            ax.set_title(chart_title, fontsize=font_title, color='#1F2937', pad=20)
            
            if len(y_axes) > 1 and chart_type not in ["円グラフ", "ヒストグラム"]:
                # 全ての軸から凡例情報を収集
                h_all, l_all = [], []
                for a_idx in sorted(axes.keys()):
                    h, l = axes[a_idx].get_legend_handles_labels()
                    h_all.extend(h)
                    l_all.extend(l)
                if h_all:
                    ax.legend(h_all, l_all)
            elif chart_type == "ヒストグラム":
                ax.legend()
                
            ax.tick_params(labelsize=font_tick_global, colors='#1F2937')
            
            # --- 目盛・グリッドの詳細設定適用 ---
            if chart_type not in ["円グラフ", "ヒストグラム", "箱ひげ図", "バイオリンプロット"]:
                # 先に補助目盛を有効化（後から呼ぶとLocatorがリセットされるため）
                if x_minor_step or y_minor_step or grid_minor:
                    ax.minorticks_on()
                
                # 目盛間隔の設定
                if x_major_step: ax.xaxis.set_major_locator(MultipleLocator(x_major_step))
                if x_minor_step: ax.xaxis.set_minor_locator(MultipleLocator(x_minor_step))
                if y_major_step: ax.yaxis.set_major_locator(MultipleLocator(y_major_step))
                if y_minor_step: ax.yaxis.set_minor_locator(MultipleLocator(y_minor_step))
                
                # 目盛自体の見た目調整
                ax.tick_params(which='major', labelsize=font_tick_global, colors='#1F2937', length=6, direction=tick_dir)
                ax.tick_params(which='minor', colors='#1F2937', length=3, direction=tick_dir)
                
                # グリッド
                if grid_major:
                    ax.grid(True, which='major', linestyle='--', alpha=0.5, color='#E5E7EB')
                else:
                    ax.grid(False, which='major')
                if grid_minor:
                    ax.grid(True, which='minor', linestyle=':', alpha=0.3, color='#E5E7EB')
                else:
                    ax.grid(False, which='minor')

            if chart_type in ["折れ線グラフ", "散布図", "棒グラフ", "複合グラフ", "ヒストグラム", "箱ひげ図", "バイオリンプロット"]:
                if xmin_val is not None: ax.set_xlim(left=xmin_val)
                if xmax_val is not None: ax.set_xlim(right=xmax_val)
                if ymin_val is not None: ax.set_ylim(bottom=ymin_val)
                if ymax_val is not None: ax.set_ylim(top=ymax_val)
                ax.set_aspect(aspect_val)
            
            # 表示
            st.pyplot(fig)
            
            # 保存とコード
            cx1, cx2 = st.columns(2)
            buf = io.BytesIO()
            fig.savefig(buf, format="png", dpi=150, bbox_inches='tight')
            cx1.download_button("📁 画像をダウンロード", buf.getvalue(), f"graph.png", "image/png")
            
            with st.expander("Python Code"):
                # データの集計ロジックをコードにも追加
                agg_snippet = ""
                if x_axis and chart_type in ["折れ線グラフ", "散布図", "棒グラフ", "複合グラフ", "円グラフ"] and not pd.api.types.is_numeric_dtype(df[x_axis]):
                    if df[x_axis].duplicated().any():
                        agg_snippet = f"plot_df = df.groupby('{x_axis}', sort=False)[{y_axes}].sum().reset_index()"
                    else:
                        agg_snippet = "plot_df = df.copy()"
                else:
                    agg_snippet = "plot_df = df.copy()"

                full_code = f"""import pandas as pd
import matplotlib.pyplot as plt
import japanize_matplotlib
import numpy as np

# データを読み込む
df = pd.read_csv('data.csv')

# 集計 (カテゴリカルなX軸で重複がある場合)
{agg_snippet}

fig, ax = plt.subplots(figsize=({width_val}, {height_val}))

{chr(10).join(code_snippets)}

ax.set_title('{chart_title}', fontsize={font_title})
"""
                if chart_type != "円グラフ":
                    full_code += f"ax.set_xlabel('{fmt(x_name, x_unit)}', fontsize={font_label_global})\n"
                
                full_code += f"ax.tick_params(labelsize={font_tick_global})\n"
                
                # 凡例のコード生成
                if len(y_axes) > 1 and chart_type not in ["円グラフ", "ヒストグラム"]:
                    full_code += """
# 全ての軸から凡例情報を収集
lines_all, labels_all = [], []
for i in range(6): # ax, ax1, ..., ax5 をチェック
    ax_name = 'ax' if i == 0 else f'ax{i}'
    if ax_name in locals():
        target_ax = locals()[ax_name]
        lns, lbs = target_ax.get_legend_handles_labels()
        lines_all.extend(lns)
        labels_all.extend(lbs)
ax.legend(lines_all, labels_all)
"""
                elif chart_type == "ヒストグラム":
                    full_code += "ax.legend()\n"
                    full_code += "from matplotlib.ticker import MultipleLocator\n"
                    if x_major_step: full_code += f"ax.xaxis.set_major_locator(MultipleLocator({x_major_step}))\n"
                    if x_minor_step: full_code += f"ax.xaxis.set_minor_locator(MultipleLocator({x_minor_step}))\n"
                    if y_major_step: full_code += f"ax.yaxis.set_major_locator(MultipleLocator({y_major_step}))\n"
                    if y_minor_step: full_code += f"ax.yaxis.set_minor_locator(MultipleLocator({y_minor_step}))\n"
                    
                    if grid_major:
                        full_code += "ax.grid(True, which='major', linestyle='--', alpha=0.3)\n"
                    if grid_minor:
                        full_code += "ax.minorticks_on()\n"
                        full_code += "ax.grid(True, which='minor', linestyle=':', alpha=0.2)\n"
                    
                    full_code += f"ax.tick_params(which='both', direction='{tick_dir}')\n"

                
                # スケール設定をコードに追加
                if chart_type in ["折れ線グラフ", "散布図", "棒グラフ", "複合グラフ", "ヒストグラム", "箱ひげ図", "バイオリンプロット"]:
                    if xmin_val is not None: full_code += f"ax.set_xlim(left={xmin_val})\n"
                    if xmax_val is not None: full_code += f"ax.set_xlim(right={xmax_val})\n"
                    if ymin_val is not None: full_code += f"ax.set_ylim(bottom={ymin_val})\n"
                    if ymax_val is not None: full_code += f"ax.set_ylim(top={ymax_val})\n"
                    if aspect_val != 'auto':
                        val_str = f"'{aspect_val}'" if isinstance(aspect_val, str) else aspect_val
                        full_code += f"ax.set_aspect({val_str})\n"

                full_code += "plt.show()"
                
                st.code(full_code, language='python')
                
        except Exception as e:
            st.error(f"グラフ生成中にエラーが発生しました: {e}")
            st.info("選択したデータが数値として正しく読み込めているか確認してください。")

else:
    # ファイル未アップロード時の表示
    st.info("👈 左側のサイドバーからCSVファイルをアップロードして始めましょう。")
    
    # 使い方ガイド
    st.markdown("""
    ### 使い方
    1. **CSVファイルをアップロード**: 左側のパネルからデータを選択します。
    2. **グラフの種類を選択**: 折れ線グラフ、棒グラフ、ヒストグラムなどから選べます。
    3. **見た目の調整**: フォントサイズや線の太さを自分好みに調整できます。
    4. **ダウンロード**: 「 画像をダウンロード」でレポートに貼れるPNGを保存できます。
    """)
    
    # サンプルデータ作成・DL機能
    st.divider()
    st.subheader("💡 サンプルデータで試す")
    st.markdown("グラフの種類に合わせたサンプルCSVをダウンロードして、使い心地を確認できます。")
    
    col_s1, col_s2, col_s3 = st.columns(3)
    
    with col_s1:
        st.write("**実験・変化データ**")
        st.caption("折れ線グラフ・散布図向き")
        # 120行の時系列データ
        rows = 120
        exp_df = pd.DataFrame({
            "時間(s)": np.arange(rows) * 5,
            "温度A(℃)": (20 + np.cumsum(np.random.normal(0.3, 0.5, rows))).round(1),
            "温度B(℃)": (18 + np.cumsum(np.random.normal(0.2, 0.4, rows))).round(1)
        })
        st.download_button("🌡️ 実験データのDL", exp_df.to_csv(index=False).encode('utf-8-sig'), "sample_experiment.csv", "text/csv")

    with col_s2:
        st.write("**分類・割合データ**")
        st.caption("棒グラフ・円グラフ向き")
        # 120行の記録データ（項目を繰り返して日付風に）
        items = ["食費", "光熱費", "通信費", "遊び", "その他"]
        rows = 120
        cat_df = pd.DataFrame({
            "通番": np.arange(1, rows + 1),
            "項目": [items[i % len(items)] for i in range(rows)],
            "金額(円)": np.random.randint(100, 5000, rows),
            "満足度": np.random.randint(1, 6, rows)
        })
        st.download_button("📊 分類データのDL", cat_df.to_csv(index=False).encode('utf-8-sig'), "sample_category.csv", "text/csv")

    with col_s3:
        st.write("**分布・統計データ**")
        st.caption("ヒスト（箱・バイオリン）向き")
        # 120行の統計用データ
        rows = 120
        np.random.seed(42)
        stat_df = pd.DataFrame({
            "グループ1": np.random.normal(70, 10, rows),
            "グループ2": np.random.normal(60, 15, rows),
            "グループ3": np.random.normal(80, 5, rows)
        }).round(1)
        st.download_button("統計データのDL", stat_df.to_csv(index=False).encode('utf-8-sig'), "sample_stats.csv", "text/csv")

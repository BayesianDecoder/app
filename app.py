import streamlit as st
import json
import os
from datetime import datetime, timedelta, date
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# ===== CONFIGURATION =====
st.set_page_config(
    page_title="Life Tracker",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom CSS
st.markdown("""
<style>
    .stButton>button {
        width: 100%;
        border-radius: 10px;
        height: 3em;
        font-weight: bold;
    }
    div[data-testid="stMetricValue"] {
        font-size: 2rem;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 24px;
    }
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        padding-left: 20px;
        padding-right: 20px;
    }
</style>
""", unsafe_allow_html=True)

# ===== DATA STORAGE =====
DATA_FILE = "life_tracker_data.json"

def load_data():
    """Load data from local file"""
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, 'r') as f:
                return json.load(f)
        except:
            return {}
    return {}

def save_data(data):
    """Save data to local file"""
    with open(DATA_FILE, 'w') as f:
        json.dump(data, f, indent=2)

def get_date_key(date_obj):
    """Convert date to string key"""
    return date_obj.strftime('%Y-%m-%d')

def get_day_data(data, date_key):
    """Get or create data structure for a specific day"""
    if date_key not in data:
        data[date_key] = {
            'workTasks': [],
            'fitness': {'duration': 0.0, 'caloriesBurnt': 0},
            'faceHealth': {'items': []},
            'diet': {'entries': [], 'totalCalories': 0},
            'energy': 3,
            'sleep': {'bedTime': '', 'wakeTime': '', 'hours': 0.0},
            'nofapStreak': 0
        }
    return data[date_key]

# ===== INITIALIZE SESSION STATE =====
if 'data' not in st.session_state:
    st.session_state.data = load_data()
    st.session_state.current_date = date.today()

# Auto-save function
def update_and_save(updates):
    """Update current day's data and save"""
    date_key = get_date_key(st.session_state.current_date)
    day_data = get_day_data(st.session_state.data, date_key)
    day_data.update(updates)
    st.session_state.data[date_key] = day_data
    save_data(st.session_state.data)

def calculate_sleep_hours(bed_time, wake_time):
    """Calculate sleep hours"""
    if not bed_time or not wake_time:
        return 0.0
    try:
        bed = datetime.strptime(bed_time, '%H:%M')
        wake = datetime.strptime(wake_time, '%H:%M')
        if wake < bed:
            wake += timedelta(days=1)
        hours = (wake - bed).total_seconds() / 3600
        return round(hours, 1)
    except:
        return 0.0

def calculate_nofap_streak(data):
    """Calculate NoFap streak"""
    streak = 0
    current = date.today()
    
    for i in range(365):
        check_date = current - timedelta(days=i)
        date_key = get_date_key(check_date)
        
        if date_key in data and data[date_key].get('nofapStreak') == 1:
            streak += 1
        elif i == 0:
            continue
        else:
            break
    
    return streak

def get_analytics_data(data, days):
    """Get analytics data for graphs"""
    stats = []
    
    for i in range(days - 1, -1, -1):
        check_date = date.today() - timedelta(days=i)
        date_key = get_date_key(check_date)
        day_data = get_day_data(data, date_key)
        
        work_mins = sum(task.get('timeSpent', 0) for task in day_data.get('workTasks', []))
        
        stats.append({
            'date': check_date,
            'date_str': check_date.strftime('%a %d'),
            'work_mins': work_mins,
            'cals_in': day_data.get('diet', {}).get('totalCalories', 0),
            'cals_out': day_data.get('fitness', {}).get('caloriesBurnt', 0),
            'sleep': day_data.get('sleep', {}).get('hours', 0),
            'energy': day_data.get('energy', 0),
            'face_total': len(day_data.get('faceHealth', {}).get('items', [])),
            'face_done': sum(1 for item in day_data.get('faceHealth', {}).get('items', []) if item.get('completed')),
            'nofap': day_data.get('nofapStreak', 0)
        })
    
    return stats

# ===== MAIN APP =====
def main():
    # Header
    col1, col2 = st.columns([3, 1])
    with col1:
        st.title("🎯 Life Tracker")
    with col2:
        st.markdown("<div style='text-align: right; color: #10b981; padding-top: 20px; font-size: 14px;'>✓ Auto-saved</div>", unsafe_allow_html=True)
    
    # Main Tabs
    tab1, tab2 = st.tabs(["📅 Today", "📊 Analytics"])
    
    # ===== TODAY TAB =====
    with tab1:
        st.write("")
        
        # Date Navigation
        col1, col2, col3 = st.columns([1, 3, 1])
        with col1:
            if st.button("⬅️ Previous Day", use_container_width=True):
                st.session_state.current_date -= timedelta(days=1)
                st.rerun()
        with col2:
            st.markdown(f"<h3 style='text-align: center;'>{st.session_state.current_date.strftime('%A, %B %d, %Y')}</h3>", unsafe_allow_html=True)
        with col3:
            if st.button("Next Day ➡️", use_container_width=True):
                st.session_state.current_date += timedelta(days=1)
                st.rerun()
        
        st.divider()
        
        current_day = get_day_data(st.session_state.data, get_date_key(st.session_state.current_date))
        
        # Top Metrics Row
        col1, col2, col3 = st.columns(3)
        
        # NoFap Streak
        with col1:
            st.markdown("### 💎 NoFap Streak")
            streak = calculate_nofap_streak(st.session_state.data)
            st.metric("Current Streak", f"{streak} days", delta="Keep going!" if streak > 0 else None)
            
            btn_label = "✓ Completed Today" if current_day['nofapStreak'] == 1 else "✅ Check In"
            btn_type = "secondary" if current_day['nofapStreak'] == 1 else "primary"
            
            if st.button(btn_label, type=btn_type, use_container_width=True, key='nofap_btn'):
                new_val = 0 if current_day['nofapStreak'] == 1 else 1
                update_and_save({'nofapStreak': new_val})
                st.rerun()
        
        # Energy Level
        with col2:
            st.markdown("### ⚡ Energy Level")
            energy = st.select_slider(
                "Rate your energy",
                options=[1, 2, 3, 4, 5],
                value=current_day['energy'],
                key='energy_slider'
            )
            if energy != current_day['energy']:
                update_and_save({'energy': energy})
            st.metric("Current Energy", f"{energy}/5")
        
        # Sleep
        with col3:
            st.markdown("### 🌙 Sleep Hours")
            bed_col, wake_col = st.columns(2)
            
            with bed_col:
                default_bed = datetime.strptime(current_day['sleep']['bedTime'], '%H:%M').time() if current_day['sleep']['bedTime'] else datetime.strptime('22:00', '%H:%M').time()
                bed_time = st.time_input("Bedtime", value=default_bed, key='bed_time')
            
            with wake_col:
                default_wake = datetime.strptime(current_day['sleep']['wakeTime'], '%H:%M').time() if current_day['sleep']['wakeTime'] else datetime.strptime('06:00', '%H:%M').time()
                wake_time = st.time_input("Wake Up", value=default_wake, key='wake_time')
            
            hours = calculate_sleep_hours(bed_time.strftime('%H:%M'), wake_time.strftime('%H:%M'))
            st.metric("Total Sleep", f"{hours}h")
            
            if bed_time.strftime('%H:%M') != current_day['sleep']['bedTime'] or wake_time.strftime('%H:%M') != current_day['sleep']['wakeTime']:
                update_and_save({
                    'sleep': {
                        'bedTime': bed_time.strftime('%H:%M'),
                        'wakeTime': wake_time.strftime('%H:%M'),
                        'hours': hours
                    }
                })
        
        st.divider()
        
        # Work Tasks Section
        st.markdown("### 💼 Work Tasks")
        
        # Add Task Form
        with st.expander("➕ Add New Task", expanded=False):
            with st.form("add_task_form", clear_on_submit=True):
                task_col1, task_col2 = st.columns([3, 1])
                with task_col1:
                    task_title = st.text_input("Task Title", placeholder="What needs to be done?")
                with task_col2:
                    task_priority = st.selectbox("Priority", ["High", "Medium", "Low"])
                
                if st.form_submit_button("Add Task", type="primary", use_container_width=True):
                    if task_title:
                        current_day['workTasks'].append({
                            'id': int(datetime.now().timestamp() * 1000),
                            'title': task_title,
                            'priority': task_priority,
                            'timeSpent': 0,
                            'completed': False
                        })
                        update_and_save(current_day)
                        st.rerun()
        
        # Display tasks
        if not current_day['workTasks']:
            st.info("No tasks for today. Add one above!")
        else:
            for idx, task in enumerate(current_day['workTasks']):
                with st.container():
                    task_col1, task_col2, task_col3, task_col4 = st.columns([0.5, 3, 1.5, 1])
                    
                    with task_col1:
                        completed = st.checkbox(
                            "✓",
                            value=task['completed'],
                            key=f"task_check_{task['id']}",
                            label_visibility="collapsed"
                        )
                        if completed != task['completed']:
                            task['completed'] = completed
                            update_and_save(current_day)
                    
                    with task_col2:
                        style = "text-decoration: line-through; color: gray;" if task['completed'] else ""
                        st.markdown(f"<p style='{style}'><b>{task['title']}</b></p>", unsafe_allow_html=True)
                    
                    with task_col3:
                        priority_colors = {'High': '🔴', 'Medium': '🟡', 'Low': '🟢'}
                        st.write(f"{priority_colors.get(task['priority'], '')} {task['priority']} | ⏱️ {task['timeSpent']}min")
                    
                    with task_col4:
                        btn_col1, btn_col2 = st.columns(2)
                        with btn_col1:
                            if st.button("+ 15", key=f"add_time_{task['id']}"):
                                task['timeSpent'] += 15
                                update_and_save(current_day)
                                st.rerun()
                        with btn_col2:
                            if st.button("🗑️", key=f"del_task_{task['id']}"):
                                current_day['workTasks'].pop(idx)
                                update_and_save(current_day)
                                st.rerun()
                    
                    st.divider()
        
        st.write("")
        
        # Bottom Row: Face Health, Diet, Fitness
        col1, col2, col3 = st.columns(3)
        
        # Face Health
        with col1:
            st.markdown("### 💧 Face Health")
            
            with st.form("add_face_form", clear_on_submit=True):
                face_item = st.text_input("Item name", placeholder="e.g., Sunscreen")
                if st.form_submit_button("Add Item", use_container_width=True):
                    if face_item:
                        current_day['faceHealth']['items'].append({
                            'id': int(datetime.now().timestamp() * 1000),
                            'name': face_item,
                            'completed': False
                        })
                        update_and_save(current_day)
                        st.rerun()
            
            if not current_day['faceHealth']['items']:
                st.info("No routine items yet")
            else:
                for item in current_day['faceHealth']['items']:
                    done = st.checkbox(
                        item['name'],
                        value=item['completed'],
                        key=f"face_{item['id']}"
                    )
                    if done != item['completed']:
                        item['completed'] = done
                        update_and_save(current_day)
        
        # Diet
        with col2:
            st.markdown("### 🍎 Diet")
            st.metric("Total Calories", current_day['diet']['totalCalories'])
            
            with st.form("add_food_form", clear_on_submit=True):
                food_name = st.text_input("Food", placeholder="e.g., Chicken Salad")
                food_cals = st.number_input("Calories", min_value=0, step=50)
                if st.form_submit_button("Add Food", use_container_width=True):
                    if food_name:
                        current_day['diet']['entries'].append({
                            'id': int(datetime.now().timestamp() * 1000),
                            'food': food_name,
                            'calories': int(food_cals)
                        })
                        current_day['diet']['totalCalories'] = sum(e['calories'] for e in current_day['diet']['entries'])
                        update_and_save(current_day)
                        st.rerun()
            
            if current_day['diet']['entries']:
                st.write("**Today's meals:**")
                for entry in current_day['diet']['entries']:
                    st.text(f"• {entry['food']}: {entry['calories']} cal")
        
        # Fitness
        with col3:
            st.markdown("### 💪 Fitness")
            
            duration = st.number_input(
                "Duration (hours)",
                min_value=0.0,
                max_value=24.0,
                step=0.5,
                value=float(current_day['fitness']['duration']),
                key='fitness_duration'
            )
            
            burnt = st.number_input(
                "Calories Burnt",
                min_value=0,
                step=50,
                value=int(current_day['fitness']['caloriesBurnt']),
                key='fitness_burnt'
            )
            
            if duration != current_day['fitness']['duration'] or burnt != current_day['fitness']['caloriesBurnt']:
                update_and_save({'fitness': {'duration': duration, 'caloriesBurnt': burnt}})
    
    # ===== ANALYTICS TAB =====
    with tab2:
        st.write("")
        
        # Timeframe selector
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            timeframe = st.radio(
                "Select timeframe",
                ['Last 7 Days', 'Last 30 Days'],
                horizontal=True,
                label_visibility="collapsed"
            )
        
        days = 7 if '7' in timeframe else 30
        stats = get_analytics_data(st.session_state.data, days)
        
        st.divider()
        
        # NoFap Consistency
        st.markdown("### 💎 NoFap Consistency")
        fig_nofap = go.Figure()
        fig_nofap.add_trace(go.Bar(
            x=[s['date_str'] for s in stats],
            y=[1 if s['nofap'] == 1 else 0.1 for s in stats],
            marker_color=['#10b981' if s['nofap'] == 1 else '#fee2e2' for s in stats],
            text=['✓' if s['nofap'] == 1 else '✗' for s in stats],
            textposition='inside',
            name='NoFap'
        ))
        fig_nofap.update_layout(
            height=200,
            showlegend=False,
            yaxis_visible=False,
            margin=dict(l=20, r=20, t=20, b=40)
        )
        st.plotly_chart(fig_nofap, use_container_width=True)
        
        # Productivity
        st.markdown("### 📊 Productivity (Work Minutes)")
        fig_work = go.Figure()
        fig_work.add_trace(go.Bar(
            x=[s['date_str'] for s in stats],
            y=[s['work_mins'] for s in stats],
            marker_color='#60a5fa',
            text=[f"{s['work_mins']}m" for s in stats],
            textposition='outside',
            name='Work Minutes'
        ))
        fig_work.update_layout(height=300, showlegend=False, margin=dict(l=20, r=20, t=40, b=40))
        st.plotly_chart(fig_work, use_container_width=True)
        
        # Sleep & Energy
        st.markdown("### 🌙 Sleep & Energy")
        fig_sleep = make_subplots(specs=[[{"secondary_y": True}]])
        fig_sleep.add_trace(
            go.Bar(
                x=[s['date_str'] for s in stats],
                y=[s['sleep'] for s in stats],
                name='Sleep (hours)',
                marker_color='#a78bfa'
            ),
            secondary_y=False
        )
        fig_sleep.add_trace(
            go.Scatter(
                x=[s['date_str'] for s in stats],
                y=[s['energy'] for s in stats],
                name='Energy (1-5)',
                marker_color='#fbbf24',
                mode='lines+markers',
                line=dict(width=3)
            ),
            secondary_y=True
        )
        fig_sleep.update_yaxes(title_text="Sleep Hours", secondary_y=False)
        fig_sleep.update_yaxes(title_text="Energy Level", secondary_y=True)
        fig_sleep.update_layout(height=350, margin=dict(l=20, r=20, t=20, b=40))
        st.plotly_chart(fig_sleep, use_container_width=True)
        
        # Calories
        st.markdown("### 🔥 Calories In vs Out")
        fig_cals = go.Figure()
        fig_cals.add_trace(go.Bar(
            x=[s['date_str'] for s in stats],
            y=[s['cals_in'] for s in stats],
            name='Consumed',
            marker_color='#fb923c'
        ))
        fig_cals.add_trace(go.Bar(
            x=[s['date_str'] for s in stats],
            y=[s['cals_out'] for s in stats],
            name='Burnt',
            marker_color='#34d399'
        ))
        fig_cals.update_layout(height=350, barmode='group', margin=dict(l=20, r=20, t=20, b=40))
        st.plotly_chart(fig_cals, use_container_width=True)
        
        # Face Health Completion Rate
        st.markdown("### 💧 Face Health Completion Rate")
        completion_rates = [
            (s['face_done'] / s['face_total'] * 100) if s['face_total'] > 0 else 0 
            for s in stats
        ]
        fig_face = go.Figure()
        fig_face.add_trace(go.Bar(
            x=[s['date_str'] for s in stats],
            y=completion_rates,
            marker_color='#ec4899',
            text=[f"{rate:.0f}%" for rate in completion_rates],
            textposition='outside'
        ))
        fig_face.update_layout(
            height=300,
            yaxis_title="Completion %",
            showlegend=False,
            margin=dict(l=20, r=20, t=20, b=40)
        )
        st.plotly_chart(fig_face, use_container_width=True)

if __name__ == "__main__":
    main()
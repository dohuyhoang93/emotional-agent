from typing import List
from src.context import AgentContext
import numpy as np
from src.logger import log, log_error # Import the new logger

def _is_stagnated(context: AgentContext, stagnation_threshold: int = 50) -> bool:
    """
    Kiểm tra xem agent có đang ở trong trạng thái "bế tắc" hay không.
    Định nghĩa "bế tắc": Tỷ lệ thành công không cải thiện trong N episode gần nhất.
    """
    # Cần có đủ dữ liệu trong bộ nhớ dài hạn (nơi lưu kết quả các episode)
    if len(context.long_term_memory.get('episode_results', [])) < stagnation_threshold:
        return False
    
    recent_results = context.long_term_memory['episode_results'][-stagnation_threshold:]
    recent_success_rate = np.mean([r['success'] for r in recent_results])
    
    # Giả sử chúng ta có một cách để lấy tỷ lệ thành công "lịch sử"
    # Để đơn giản, chúng ta so sánh với một ngưỡng cứng. Nếu tỷ lệ thành công gần đây
    # quá thấp, coi như là bế tắc.
    # Một logic phức tạp hơn có thể so sánh với các giai đoạn trước đó.
    # --- STRATEGY 2: AGGRESSIVE SOCIAL LEARNING ---
    # 1. Tăng ngưỡng bế tắc lên 10% (thay vì 5%)
    if recent_success_rate < 0.05: 
        return True
    
    # 2. Kích hoạt định kỳ mỗi 500 episode (thay vì 50) để giảm nhiễu
    if context.current_episode % 500 == 0:
        return True

    return False

def social_learning(context: AgentContext, all_contexts: List[AgentContext], agent_id: int) -> AgentContext:
    """
    Process cho phép agent học hỏi từ các agent khác khi bị bế tắc.
    """
    if not _is_stagnated(context):
        return context
    
    # [CONTROL GROUP CHECK]
    # Nếu assimilation_rate <= 0, tắt hoàn toàn tính năng học xã hội.
    # Điều này giúp ta chạy các thử nghiệm đối chứng (Control Group) để đo lường hiệu quả thực sự.
    if context.assimilation_rate <= 0:
        return context

    log(context, "info", f"  [P] 9. Agent {agent_id} is stagnated, attempting social learning...")

    # 1. Tìm agent thành công nhất (không phải chính mình)
    best_agent_context = None
    max_success_rate = -1.0

    for i, other_context in enumerate(all_contexts):
        if i == agent_id:
            continue
        
        # Lấy tỷ lệ thành công của agent khác từ bộ nhớ của nó
        other_results = other_context.long_term_memory.get('episode_results', [])
        if not other_results:
            continue
            
        other_success_rate = np.mean([r['success'] for r in other_results])
        if other_success_rate > max_success_rate:
            max_success_rate = other_success_rate
            best_agent_context = other_context

    # 2. Nếu tìm thấy agent tốt hơn, đồng hóa một phần kiến thức (Học hỏi Tích cực)
    if best_agent_context and max_success_rate > np.mean([r['success'] for r in context.long_term_memory.get('episode_results', [])]):
        log(context, "verbose", f"    > Found better agent {all_contexts.index(best_agent_context)} with success rate {max_success_rate:.2f}. Assimilating Q-table...")
        
        assimilation_rate = context.assimilation_rate # Sử dụng giá trị từ cấu hình (mặc định 0.1)

        for state, actions in best_agent_context.q_table.items():
            if state not in context.q_table:
                context.q_table[state] = actions.copy()
            else:
                for action, q_value in actions.items():
                    current_q = context.q_table[state].get(action, 0.0)
                    context.q_table[state][action] = (1 - assimilation_rate) * current_q + assimilation_rate * q_value
    else:
        log(context, "verbose", "    > No better agent found to learn from.")

    # --- Logic Mới: Học hỏi Tiêu cực từ agent tệ nhất ---
    # 3. Tìm agent tệ nhất
    worst_agent_context = None
    min_success_rate = 1.1 # Bắt đầu với giá trị lớn hơn 1.0

    for i, other_context in enumerate(all_contexts):
        if i == agent_id:
            continue
        
        other_results = other_context.long_term_memory.get('episode_results', [])
        if not other_results:
            continue
            
        other_success_rate = np.mean([r['success'] for r in other_results])
        if other_success_rate < min_success_rate:
            min_success_rate = other_success_rate
            worst_agent_context = other_context

    # 4. Nếu tìm thấy agent tệ hơn, học cách tránh sai lầm của nó
    if worst_agent_context and min_success_rate < np.mean([r['success'] for r in context.long_term_memory.get('episode_results', [])]):
        log(context, "verbose", f"    > [Aversive Learning] Found worse agent {all_contexts.index(worst_agent_context)} with success rate {min_success_rate:.2f}. Avoiding mistakes...")
        
        MISTAKE_THRESHOLD = -1.0 # Ngưỡng Q-value được coi là một sai lầm
        PUNISHMENT_VALUE = -10.0 # Giá trị trừng phạt để ghi đè

        for state, actions in worst_agent_context.q_table.items():
            for action, q_value in actions.items():
                if q_value < MISTAKE_THRESHOLD:
                    if state not in context.q_table or context.q_table[state].get(action, 0.0) > MISTAKE_THRESHOLD:
                        if state not in context.q_table:
                            context.q_table[state] = {}
                        context.q_table[state][action] = PUNISHMENT_VALUE
    # ----------------------------------------------------

    return context

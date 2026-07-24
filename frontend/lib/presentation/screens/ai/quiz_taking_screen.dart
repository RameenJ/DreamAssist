import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import '../../providers/ai_quiz_provider.dart';
import '../../providers/auth_provider.dart';
import '../../../core/theme/app_theme.dart';

class QuizTakingScreen extends ConsumerStatefulWidget {
  final String bookId;

  const QuizTakingScreen({super.key, required this.bookId});

  @override
  ConsumerState<QuizTakingScreen> createState() => _QuizTakingScreenState();
}

class _QuizTakingScreenState extends ConsumerState<QuizTakingScreen> {
  final Map<int, TextEditingController> _controllers = {};
  final Map<int, FocusNode> _focusNodes = {};

  @override
  void dispose() {
    for (var controller in _controllers.values) {
      controller.dispose();
    }
    for (var focusNode in _focusNodes.values) {
      focusNode.dispose();
    }
    super.dispose();
  }

  TextEditingController _getController(int index, String? currentAnswer) {
    if (!_controllers.containsKey(index)) {
      _controllers[index] = TextEditingController(text: currentAnswer ?? '');
    }
    return _controllers[index]!;
  }

  FocusNode _getFocusNode(int index) {
    if (!_focusNodes.containsKey(index)) {
      _focusNodes[index] = FocusNode();
    }
    return _focusNodes[index]!;
  }

  @override
  Widget build(BuildContext context) {
    final quizState = ref.watch(aiQuizProvider);

    if (quizState.currentQuiz == null) {
      return Scaffold(
        appBar: AppBar(title: const Text('Quiz')),
        body: const Center(
          child: Text('No active quiz found'),
        ),
      );
    }

    final quiz = quizState.currentQuiz!;
    final currentQuestion = quiz.questions[quiz.currentQuestionIndex];
    final currentAnswer = quiz.userAnswers[quiz.currentQuestionIndex];

    // Get user's weak topics from subject profile (if available)
    List<String> weakTopics = [];
    final authState = ref.watch(authProvider);
    final user = authState.user;
    if (user != null && user.subjectProfiles != null) {
      final profiles = user.subjectProfiles!.where((sp) => sp.subject == quiz.topicName);
      if (profiles.isNotEmpty) {
        final profile = profiles.first;
        if (profile.weakTopics != null) {
          weakTopics = profile.weakTopics!;
        }
      }
    }
    final progress = ref.read(aiQuizProvider.notifier).getProgress();

    return WillPopScope(
      onWillPop: () async {
        final shouldPop = await showDialog<bool>(
          context: context,
          builder: (context) => AlertDialog(
            title: const Text('Exit Quiz?'),
            content: const Text('Your progress will be lost if you exit now.'),
            actions: [
              TextButton(
                onPressed: () => Navigator.pop(context, false),
                child: const Text('Continue Quiz'),
              ),
              TextButton(
                onPressed: () => Navigator.pop(context, true),
                child: const Text('Exit'),
              ),
            ],
          ),
        );
        return shouldPop ?? false;
      },
      child: Scaffold(
        appBar: AppBar(
          title: Text('Question ${quiz.currentQuestionIndex + 1}/${quiz.questions.length}'),
          bottom: PreferredSize(
            preferredSize: const Size.fromHeight(4),
            child: LinearProgressIndicator(
              value: progress,
              backgroundColor: Colors.grey.shade200,
            ),
          ),
        ),
        body: Column(
          children: [
            // Question card
            Expanded(
              child: SingleChildScrollView(
                padding: const EdgeInsets.all(16),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.stretch,
                  children: [
                    // Question
                    Card(
                      child: Padding(
                        padding: const EdgeInsets.all(20),
                        child: Text(
                          currentQuestion.questionText,
                          style: Theme.of(context).textTheme.titleLarge?.copyWith(
                                height: 1.5,
                                fontWeight: FontWeight.bold,
                              ),
                        ),
                      ),
                    ),

                    const SizedBox(height: 16),

                    // Answer input
                    Text(
                      'Type your answer:',
                      style: Theme.of(context).textTheme.titleSmall?.copyWith(
                            color: AppTheme.textSecondary,
                          ),
                    ),
                    const SizedBox(height: 12),

                    Card(
                      child: Padding(
                        padding: const EdgeInsets.all(16),
                        child: TextField(
                          controller: _getController(quiz.currentQuestionIndex, currentAnswer),
                          focusNode: _getFocusNode(quiz.currentQuestionIndex),
                          decoration: InputDecoration(
                            hintText: 'Enter your answer here...',
                            border: OutlineInputBorder(
                              borderRadius: BorderRadius.circular(8),
                            ),
                            filled: true,
                            fillColor: Colors.grey.shade50,
                          ),
                          maxLines: 3,
                          onChanged: (value) {
                            ref.read(aiQuizProvider.notifier).answerQuestion(
                                  quiz.currentQuestionIndex,
                                  value,
                                );
                          },
                        ),
                      ),
                    ),

                    const SizedBox(height: 16),

                    // Hint card
                    Card(
                      color: AppTheme.primaryColor.withValues(alpha: 0.1),
                      child: Padding(
                        padding: const EdgeInsets.all(16),
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Row(
                              children: [
                                const Icon(
                                  Icons.lightbulb_outline,
                                  size: 20,
                                  color: AppTheme.primaryColor,
                                ),
                                const SizedBox(width: 8),
                                Text(
                                  'Hint',
                                  style: Theme.of(context).textTheme.titleSmall?.copyWith(
                                        fontWeight: FontWeight.bold,
                                        color: AppTheme.primaryColor,
                                      ),
                                ),
                              ],
                            ),
                            const SizedBox(height: 8),
                            const Text(
                              'Type your answer based on what you learned from the book. Be concise and accurate.',
                              style: TextStyle(fontSize: 13),
                            ),
                            // Show extra hint if question is related to a weak topic
                            if (weakTopics.any((topic) => currentQuestion.questionText.toLowerCase().contains(topic.toLowerCase()))) ...[
                              const SizedBox(height: 8),
                              const Row(
                                children: [
                                  Icon(Icons.warning_amber, color: Colors.orange, size: 18),
                                  SizedBox(width: 6),
                                  Expanded(
                                    child: Text(
                                      'AI Tutor: This question is from a topic you struggled with. Pay extra attention and review your notes!',
                                      style: TextStyle(color: Colors.orange, fontWeight: FontWeight.bold, fontSize: 13),
                                    ),
                                  ),
                                ],
                              ),
                            ],
                          ],
                        ),
                      ),
                    ),
                  ],
                ),
              ),
            ),

            // Navigation buttons
            Container(
              padding: const EdgeInsets.all(16),
              decoration: BoxDecoration(
                color: Theme.of(context).cardColor,
                boxShadow: [
                  BoxShadow(
                    color: Colors.black.withValues(alpha: 0.1),
                    blurRadius: 4,
                    offset: const Offset(0, -2),
                  ),
                ],
              ),
              child: SafeArea(
                child: Row(
                  children: [
                    // Previous button
                    if (quiz.currentQuestionIndex > 0)
                      OutlinedButton.icon(
                        onPressed: () {
                          ref.read(aiQuizProvider.notifier).previousQuestion();
                        },
                        icon: const Icon(Icons.arrow_back),
                        label: const Text('Previous'),
                      ),

                    const Spacer(),

                    // Question navigator
                    TextButton(
                      onPressed: () => _showQuestionNavigator(context, ref, quiz),
                      child: Text(
                        '${quiz.currentQuestionIndex + 1}/${quiz.questions.length}',
                      ),
                    ),

                    const Spacer(),

                    // Next/Submit button
                    if (quiz.currentQuestionIndex < quiz.questions.length - 1)
                      ElevatedButton.icon(
                        onPressed: () {
                          ref.read(aiQuizProvider.notifier).nextQuestion();
                        },
                        icon: const Icon(Icons.arrow_forward),
                        label: const Text('Next'),
                      )
                    else
                      ElevatedButton.icon(
                        onPressed: () => _submitQuiz(context, ref),
                        icon: const Icon(Icons.check),
                        label: const Text('Submit'),
                        style: ElevatedButton.styleFrom(
                          backgroundColor: Colors.green,
                        ),
                      ),
                  ],
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }

  void _showQuestionNavigator(BuildContext context, WidgetRef ref, QuizAttempt quiz) {
    showModalBottomSheet(
      context: context,
      builder: (context) => Container(
        padding: const EdgeInsets.all(16),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              'Jump to Question',
              style: Theme.of(context).textTheme.titleLarge?.copyWith(
                    fontWeight: FontWeight.bold,
                  ),
            ),
            const SizedBox(height: 16),
            Wrap(
              spacing: 8,
              runSpacing: 8,
              children: List.generate(
                quiz.questions.length,
                (index) {
                  final answer = quiz.userAnswers[index];
                  final isAnswered = answer != null && answer.trim().isNotEmpty;
                  final isCurrent = index == quiz.currentQuestionIndex;

                  return InkWell(
                    onTap: () {
                      ref.read(aiQuizProvider.notifier).goToQuestion(index);
                      Navigator.pop(context);
                    },
                    child: Container(
                      width: 50,
                      height: 50,
                      decoration: BoxDecoration(
                        color: isCurrent
                            ? AppTheme.primaryColor
                            : isAnswered
                                ? Colors.green.shade100
                                : Colors.grey.shade200,
                        borderRadius: BorderRadius.circular(8),
                        border: Border.all(
                          color: isCurrent
                              ? AppTheme.primaryColor
                              : isAnswered
                                  ? Colors.green
                                  : Colors.grey,
                          width: 2,
                        ),
                      ),
                      child: Center(
                        child: Text(
                          '${index + 1}',
                          style: TextStyle(
                            color: isCurrent ? Colors.white : Colors.black87,
                            fontWeight: FontWeight.bold,
                          ),
                        ),
                      ),
                    ),
                  );
                },
              ),
            ),
            const SizedBox(height: 16),
            Row(
              children: [
                _buildLegendItem(Colors.green.shade100, 'Answered'),
                const SizedBox(width: 16),
                _buildLegendItem(Colors.grey.shade200, 'Not Answered'),
              ],
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildLegendItem(Color color, String label) {
    return Row(
      mainAxisSize: MainAxisSize.min,
      children: [
        Container(
          width: 20,
          height: 20,
          decoration: BoxDecoration(
            color: color,
            borderRadius: BorderRadius.circular(4),
          ),
        ),
        const SizedBox(width: 8),
        Text(label, style: const TextStyle(fontSize: 12)),
      ],
    );
  }

  Future<void> _submitQuiz(BuildContext context, WidgetRef ref) async {
    print('👉 [SUBMIT BUTTON] Submit quiz button clicked');
    final quiz = ref.read(aiQuizProvider).currentQuiz!;
    final unanswered = quiz.userAnswers.where((a) => a == null || a.trim().isEmpty).length;

    print('👉 [SUBMIT BUTTON] Unanswered questions: $unanswered');

    if (unanswered > 0) {
      print('⚠️ [SUBMIT BUTTON] Showing unanswered warning dialog');
      final shouldSubmit = await showDialog<bool>(
        context: context,
        builder: (context) => AlertDialog(
          title: const Text('Submit Quiz?'),
          content: Text(
            'You have $unanswered unanswered question(s). Do you want to submit anyway?',
          ),
          actions: [
            TextButton(
              onPressed: () => Navigator.pop(context, false),
              child: const Text('Review'),
            ),
            TextButton(
              onPressed: () => Navigator.pop(context, true),
              child: const Text('Submit'),
            ),
          ],
        ),
      );

      if (shouldSubmit != true) {
        print('👉 [SUBMIT BUTTON] User chose to review answers');
        return;
      }
    }

    print('✅ [SUBMIT BUTTON] Calling submitQuiz()...');
    final success = await ref.read(aiQuizProvider.notifier).submitQuiz();
    
    print('👉 [SUBMIT BUTTON] Submit result: $success');
    print('👉 [SUBMIT BUTTON] Context mounted: ${context.mounted}');
    
    if (!mounted) {
      print('❌ [SUBMIT BUTTON] Widget no longer mounted');
      return;
    }
    
    if (success) {
      print('✅ [SUBMIT BUTTON] Quiz evaluated successfully, navigating to results...');
      // The provider has already updated state with evaluation before returning true
      final quizState = ref.read(aiQuizProvider);
      print('🎯 [SUBMIT BUTTON] Has evaluation: ${quizState.currentQuiz?.evaluation != null}');
      
      // Navigate to results screen - use pushReplacement to replace quiz taking screen
      if (context.mounted) {
        print('🚀 [SUBMIT BUTTON] Attempting navigation to /quiz/results');
        context.pushReplacement('/quiz/results');
        print('✅ [SUBMIT BUTTON] Navigation called successfully');
      } else {
        print('❌ [SUBMIT BUTTON] Context not mounted, cannot navigate');
      }
    } else {
      print('❌ [SUBMIT BUTTON] Submission failed');
      if (mounted && context.mounted) {
        final error = ref.read(aiQuizProvider).error;
        print('❌ [SUBMIT BUTTON] Error: $error');
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text(error ?? 'Failed to submit quiz'),
            backgroundColor: Colors.red,
            duration: const Duration(seconds: 5),
          ),
        );
      }
    }
  }
}

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import '../../providers/ai_quiz_provider.dart';
import '../../../core/theme/app_theme.dart';

class QuizResultsScreen extends ConsumerWidget {
  const QuizResultsScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    print('📊 [RESULTS SCREEN] Building results screen...');
    final quizState = ref.watch(aiQuizProvider);
    
    print('📊 [RESULTS SCREEN] Current quiz: ${quizState.currentQuiz != null ? "EXISTS" : "NULL"}');
    print('📊 [RESULTS SCREEN] Evaluation: ${quizState.currentQuiz?.evaluation != null ? "EXISTS" : "NULL"}');
    print('📊 [RESULTS SCREEN] Is loading: ${quizState.isLoading}');

    // Show loading while evaluation is being processed
    if (quizState.isLoading) {
      return Scaffold(
        appBar: AppBar(title: const Text('Quiz Results')),
        body: const Center(
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              CircularProgressIndicator(),
              SizedBox(height: 16),
              Text('Evaluating your answers...'),
            ],
          ),
        ),
      );
    }

    if (quizState.currentQuiz == null || quizState.currentQuiz!.evaluation == null) {
      print('❌ [RESULTS SCREEN] No quiz or evaluation found!');
      // Show a message instead of auto-redirecting
      return Scaffold(
        appBar: AppBar(
          title: const Text('Quiz Results'),
          leading: IconButton(
            icon: const Icon(Icons.arrow_back),
            onPressed: () => context.go('/home'),
          ),
        ),
        body: Center(
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              const Icon(Icons.error_outline, size: 64, color: Colors.orange),
              const SizedBox(height: 16),
              const Text(
                'No quiz results available',
                style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
              ),
              const SizedBox(height: 8),
              const Text('Please take a quiz first'),
              const SizedBox(height: 24),
              ElevatedButton(
                onPressed: () => context.go('/home'),
                child: const Text('Go to Home'),
              ),
            ],
          ),
        ),
      );
    }

    final quiz = quizState.currentQuiz!;
    final evaluation = quiz.evaluation!;
    final totalQuestions = evaluation.results.length;
    final percentage = (evaluation.totalScore * 100).round();
    
    // Calculate correct and wrong answers
    int correctAnswers = 0;
    int wrongAnswers = 0;
    for (var result in evaluation.results) {
      if (result.similarityScore >= 0.7) {
        correctAnswers++;
      } else {
        wrongAnswers++;
      }
    }
    
    print('✅ [RESULTS SCREEN] Displaying results - Score: $percentage%, Grade: ${evaluation.totalGrade}, Correct: $correctAnswers, Wrong: $wrongAnswers');

    // Show AI Tutor's attention message if weak topics exist
    if (evaluation.weakTopics != null && evaluation.weakTopics!.isNotEmpty) {
      WidgetsBinding.instance.addPostFrameCallback((_) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Row(
              children: [
                const Icon(Icons.psychology, color: Colors.orange, size: 24),
                const SizedBox(width: 8),
                Expanded(
                  child: Text(
                    'AI Tutor: Pay extra attention to: ${evaluation.weakTopics!.join(", ")}',
                    style: const TextStyle(fontWeight: FontWeight.bold),
                  ),
                ),
              ],
            ),
            backgroundColor: Colors.orange.shade100,
            behavior: SnackBarBehavior.floating,
            duration: const Duration(seconds: 6),
          ),
        );
      });
    }

    return Scaffold(
      appBar: AppBar(
        title: const Text('Quiz Results'),
        leading: IconButton(
          icon: const Icon(Icons.close),
          onPressed: () {
            ref.read(aiQuizProvider.notifier).clearQuiz();
            context.go('/home');
          },
        ),
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            // Score card
            Card(
              elevation: 4,
              child: Padding(
                padding: const EdgeInsets.all(24),
                child: Column(
                  children: [
                    Icon(
                      _getScoreIcon(percentage),
                      size: 80,
                      color: _getScoreColor(percentage),
                    ),
                    const SizedBox(height: 16),
                    Text(
                      _getScoreMessage(percentage),
                      style: Theme.of(context).textTheme.headlineSmall?.copyWith(
                            fontWeight: FontWeight.bold,
                            color: _getScoreColor(percentage),
                          ),
                      textAlign: TextAlign.center,
                    ),
                    const SizedBox(height: 16),
                    Row(
                      mainAxisAlignment: MainAxisAlignment.center,
                      crossAxisAlignment: CrossAxisAlignment.baseline,
                      textBaseline: TextBaseline.alphabetic,
                      children: [
                        Text(
                          '$percentage',
                          style: Theme.of(context).textTheme.displayLarge?.copyWith(
                                fontWeight: FontWeight.bold,
                                color: _getScoreColor(percentage),
                              ),
                        ),
                        Text(
                          '%',
                          style: Theme.of(context).textTheme.headlineMedium?.copyWith(
                                color: _getScoreColor(percentage),
                              ),
                        ),
                      ],
                    ),
                    const SizedBox(height: 8),
                    Text(
                      'Overall Grade: ${evaluation.totalGrade}',
                      style: Theme.of(context).textTheme.titleMedium?.copyWith(
                            color: AppTheme.textSecondary,
                          ),
                    ),
                  ],
                ),
              ),
            ),

            const SizedBox(height: 24),

            // Statistics
            Row(
              children: [
                Expanded(
                  child: _buildStatCard(
                    context,
                    'Total',
                    totalQuestions.toString(),
                    Icons.quiz,
                    AppTheme.accentColor,
                  ),
                ),
                const SizedBox(width: 12),
                Expanded(
                  child: _buildStatCard(
                    context,
                    'Correct',
                    correctAnswers.toString(),
                    Icons.check_circle,
                    Colors.green,
                  ),
                ),
                const SizedBox(width: 12),
                Expanded(
                  child: _buildStatCard(
                    context,
                    'Wrong',
                    wrongAnswers.toString(),
                    Icons.cancel,
                    Colors.red,
                  ),
                ),
              ],
            ),
            
            const SizedBox(height: 12),
            
            // Overall grade card
            Card(
              color: AppTheme.primaryColor.withValues(alpha: 0.1),
              child: Padding(
                padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
                child: Row(
                  mainAxisAlignment: MainAxisAlignment.center,
                  children: [
                    const Icon(Icons.emoji_events, color: AppTheme.primaryColor, size: 24),
                    const SizedBox(width: 8),
                    Text(
                      'Grade: ${evaluation.totalGrade}',
                      style: Theme.of(context).textTheme.titleLarge?.copyWith(
                            fontWeight: FontWeight.bold,
                            color: AppTheme.primaryColor,
                          ),
                    ),
                  ],
                ),
              ),
            ),

            const SizedBox(height: 24),

            // AI Mentor Recommendations Section
            if (evaluation.studyRecommendations != null) ...[
              // Header
              Row(
                children: [
                  const Icon(Icons.psychology, color: AppTheme.primaryColor, size: 28),
                  const SizedBox(width: 8),
                  Text(
                    'Your AI Mentor Says:',
                    style: Theme.of(context).textTheme.titleLarge?.copyWith(
                      fontWeight: FontWeight.bold,
                      color: AppTheme.primaryColor,
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 12),
              
              // Study Recommendations Card
              Card(
                elevation: 3,
                color: Colors.blue.shade50,
                child: Padding(
                  padding: const EdgeInsets.all(16),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Row(
                        children: [
                          const Icon(Icons.lightbulb, color: Colors.orange, size: 20),
                          const SizedBox(width: 8),
                          Text(
                            'Personalized Study Plan',
                            style: Theme.of(context).textTheme.titleMedium?.copyWith(
                              fontWeight: FontWeight.bold,
                            ),
                          ),
                        ],
                      ),
                      const SizedBox(height: 12),
                      Text(
                        evaluation.studyRecommendations!,
                        style: Theme.of(context).textTheme.bodyLarge,
                      ),
                    ],
                  ),
                ),
              ),
              
              const SizedBox(height: 16),
              
              // Weak Topics
              if (evaluation.weakTopics?.isNotEmpty ?? false) ...[
                Row(
                  children: [
                    const Icon(Icons.warning_amber, color: Colors.orange, size: 20),
                    const SizedBox(width: 8),
                    Text(
                      'Focus On These Topics:',
                      style: Theme.of(context).textTheme.titleMedium?.copyWith(
                        fontWeight: FontWeight.bold,
                      ),
                    ),
                  ],
                ),
                const SizedBox(height: 8),
                Wrap(
                  spacing: 8,
                  runSpacing: 8,
                  children: evaluation.weakTopics!.map((topic) => Chip(
                    label: Text(topic),
                    backgroundColor: Colors.orange.shade100,
                    avatar: const Icon(Icons.flag, size: 16),
                  )).toList(),
                ),
                const SizedBox(height: 16),
              ],
              
              // Strong Topics
              if (evaluation.strongTopics?.isNotEmpty ?? false) ...[
                Row(
                  children: [
                    const Icon(Icons.check_circle, color: Colors.green, size: 20),
                    const SizedBox(width: 8),
                    Text(
                      'You Know These Well:',
                      style: Theme.of(context).textTheme.titleMedium?.copyWith(
                        fontWeight: FontWeight.bold,
                      ),
                    ),
                  ],
                ),
                const SizedBox(height: 8),
                Wrap(
                  spacing: 8,
                  runSpacing: 8,
                  children: evaluation.strongTopics!.map((topic) => Chip(
                    label: Text(topic),
                    backgroundColor: Colors.green.shade100,
                    avatar: const Icon(Icons.star, size: 16),
                  )).toList(),
                ),
                const SizedBox(height: 16),
              ],
              
              // Next Steps
              if (evaluation.nextSteps?.isNotEmpty ?? false) ...[
                Row(
                  children: [
                    const Icon(Icons.task_alt, color: AppTheme.primaryColor, size: 20),
                    const SizedBox(width: 8),
                    Text(
                      'Action Plan:',
                      style: Theme.of(context).textTheme.titleMedium?.copyWith(
                        fontWeight: FontWeight.bold,
                      ),
                    ),
                  ],
                ),
                const SizedBox(height: 8),
                Card(
                  child: Padding(
                    padding: const EdgeInsets.all(12),
                    child: Column(
                      children: evaluation.nextSteps!.asMap().entries.map((entry) => 
                        Padding(
                          padding: const EdgeInsets.only(bottom: 8),
                          child: Row(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              Container(
                                width: 24,
                                height: 24,
                                decoration: BoxDecoration(
                                  color: AppTheme.primaryColor,
                                  borderRadius: BorderRadius.circular(12),
                                ),
                                child: Center(
                                  child: Text(
                                    '${entry.key + 1}',
                                    style: const TextStyle(
                                      color: Colors.white,
                                      fontWeight: FontWeight.bold,
                                      fontSize: 12,
                                    ),
                                  ),
                                ),
                              ),
                              const SizedBox(width: 12),
                              Expanded(
                                child: Text(
                                  entry.value,
                                  style: Theme.of(context).textTheme.bodyMedium,
                                ),
                              ),
                            ],
                          ),
                        ),
                      ).toList(),
                    ),
                  ),
                ),
                const SizedBox(height: 16),
              ],
              
              const Divider(height: 32, thickness: 2),
            ],

            // Review answers
            Text(
              'Review Answers',
              style: Theme.of(context).textTheme.titleLarge?.copyWith(
                    fontWeight: FontWeight.bold,
                  ),
            ),
            const SizedBox(height: 12),

            ...List.generate(
              quiz.questions.length,
              (index) => _buildAnswerReviewCard(
                context,
                quiz.questions[index].questionText,
                quiz.userAnswers[index] ?? '',
                evaluation.results[index],
                index + 1,
              ),
            ),

            const SizedBox(height: 24),

            // Actions
            ElevatedButton.icon(
              onPressed: () {
                ref.read(aiQuizProvider.notifier).resetQuiz();
                context.pop();
              },
              icon: const Icon(Icons.refresh),
              label: const Text('Retake Quiz'),
              style: ElevatedButton.styleFrom(
                padding: const EdgeInsets.symmetric(vertical: 16),
              ),
            ),
            const SizedBox(height: 8),
            OutlinedButton.icon(
              onPressed: () {
                ref.read(aiQuizProvider.notifier).clearQuiz();
                context.go('/home');
              },
              icon: const Icon(Icons.home),
              label: const Text('Back to Home'),
              style: OutlinedButton.styleFrom(
                padding: const EdgeInsets.symmetric(vertical: 16),
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildStatCard(
    BuildContext context,
    String label,
    String value,
    IconData icon,
    Color color,
  ) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          children: [
            Icon(icon, color: color, size: 32),
            const SizedBox(height: 8),
            Text(
              value,
              style: Theme.of(context).textTheme.headlineMedium?.copyWith(
                    fontWeight: FontWeight.bold,
                    color: color,
                  ),
            ),
            Text(
              label,
              style: Theme.of(context).textTheme.bodySmall?.copyWith(
                    color: AppTheme.textSecondary,
                  ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildAnswerReviewCard(
    BuildContext context,
    String question,
    String userAnswer,
    result,
    int questionNumber,
  ) {
    final similarityScore = result.similarityScore;
    final isCorrect = similarityScore >= 0.7; // Consider 70% similarity as correct
    final scorePercentage = (similarityScore * 100).round();

    return Card(
      margin: const EdgeInsets.only(bottom: 12),
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // Question header
            Row(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                  decoration: BoxDecoration(
                    color: isCorrect
                        ? Colors.green.withValues(alpha: 0.1)
                        : Colors.orange.withValues(alpha: 0.1),
                    borderRadius: BorderRadius.circular(8),
                  ),
                  child: Row(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      Icon(
                        isCorrect ? Icons.check_circle : Icons.info_outline,
                        size: 16,
                        color: isCorrect ? Colors.green : Colors.orange,
                      ),
                      const SizedBox(width: 4),
                      Text(
                        'Q$questionNumber',
                        style: TextStyle(
                          fontWeight: FontWeight.bold,
                          color: isCorrect ? Colors.green : Colors.orange,
                        ),
                      ),
                    ],
                  ),
                ),
                const Spacer(),
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                  decoration: BoxDecoration(
                    color: _getScoreColor(scorePercentage).withValues(alpha: 0.1),
                    borderRadius: BorderRadius.circular(8),
                  ),
                  child: Text(
                    'Score: $scorePercentage%',
                    style: TextStyle(
                      fontWeight: FontWeight.bold,
                      color: _getScoreColor(scorePercentage),
                    ),
                  ),
                ),
              ],
            ),
            const SizedBox(height: 12),

            // Question text
            Text(
              question,
              style: Theme.of(context).textTheme.titleSmall?.copyWith(
                    fontWeight: FontWeight.w600,
                  ),
            ),
            const SizedBox(height: 12),

            // User's answer
            Container(
              padding: const EdgeInsets.all(12),
              decoration: BoxDecoration(
                color: Colors.blue.withValues(alpha: 0.05),
                border: Border.all(color: Colors.blue.withValues(alpha: 0.3)),
                borderRadius: BorderRadius.circular(8),
              ),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(
                    children: [
                      const Icon(Icons.person, size: 16, color: Colors.blue),
                      const SizedBox(width: 4),
                      Text(
                        'Your Answer:',
                        style: Theme.of(context).textTheme.bodySmall?.copyWith(
                              fontWeight: FontWeight.bold,
                              color: Colors.blue,
                            ),
                      ),
                    ],
                  ),
                  const SizedBox(height: 4),
                  Text(
                    userAnswer.isEmpty ? '(Not answered)' : userAnswer,
                    style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                          fontStyle: userAnswer.isEmpty ? FontStyle.italic : null,
                        ),
                  ),
                ],
              ),
            ),
            const SizedBox(height: 8),

            // Correct answer
            Container(
              padding: const EdgeInsets.all(12),
              decoration: BoxDecoration(
                color: Colors.green.withValues(alpha: 0.05),
                border: Border.all(color: Colors.green.withValues(alpha: 0.3)),
                borderRadius: BorderRadius.circular(8),
              ),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(
                    children: [
                      const Icon(Icons.check_circle, size: 16, color: Colors.green),
                      const SizedBox(width: 4),
                      Text(
                        'Correct Answer:',
                        style: Theme.of(context).textTheme.bodySmall?.copyWith(
                              fontWeight: FontWeight.bold,
                              color: Colors.green,
                            ),
                      ),
                    ],
                  ),
                  const SizedBox(height: 4),
                  Text(
                    result.correctAnswer,
                    style: Theme.of(context).textTheme.bodyMedium,
                  ),
                ],
              ),
            ),

            // Explanation
            if (result.correctExplanation != null && result.correctExplanation!.isNotEmpty) ...[
              const SizedBox(height: 8),
              Container(
                padding: const EdgeInsets.all(12),
                decoration: BoxDecoration(
                  color: Colors.grey.shade50,
                  borderRadius: BorderRadius.circular(8),
                ),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Row(
                      children: [
                        Icon(Icons.lightbulb, size: 16, color: Colors.amber.shade700),
                        const SizedBox(width: 4),
                        Text(
                          'Explanation:',
                          style: Theme.of(context).textTheme.bodySmall?.copyWith(
                                fontWeight: FontWeight.bold,
                                color: Colors.amber.shade700,
                              ),
                        ),
                      ],
                    ),
                    const SizedBox(height: 4),
                    Text(
                      result.correctExplanation!,
                      style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                            color: AppTheme.textSecondary,
                          ),
                    ),
                  ],
                ),
              ),
            ],
          ],
        ),
      ),
    );
  }

  IconData _getScoreIcon(int percentage) {
    if (percentage >= 80) return Icons.emoji_events;
    if (percentage >= 60) return Icons.thumb_up;
    if (percentage >= 40) return Icons.sentiment_neutral;
    return Icons.sentiment_dissatisfied;
  }

  Color _getScoreColor(int percentage) {
    if (percentage >= 80) return Colors.green;
    if (percentage >= 60) return Colors.orange;
    return Colors.red;
  }

  String _getScoreMessage(int percentage) {
    if (percentage >= 90) return 'Outstanding!';
    if (percentage >= 80) return 'Excellent Work!';
    if (percentage >= 70) return 'Good Job!';
    if (percentage >= 60) return 'Not Bad!';
    if (percentage >= 50) return 'Keep Practicing!';
    return 'Try Again!';
  }
}

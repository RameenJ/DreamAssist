import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../../core/theme/app_theme.dart';
import '../../../data/models/ai_model.dart';
import '../../providers/ai_history_provider.dart';

class QuizHistoryScreen extends ConsumerStatefulWidget {
  final String? bookId;
  final String? bookTitle;

  const QuizHistoryScreen({
    this.bookId,
    this.bookTitle,
    super.key,
  });

  @override
  ConsumerState<QuizHistoryScreen> createState() => _QuizHistoryScreenState();
}

class _QuizHistoryScreenState extends ConsumerState<QuizHistoryScreen> {
  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (widget.bookId != null) {
        ref
            .read(quizHistoryProvider.notifier)
            .loadQuizHistoryByBook(widget.bookId!);
      } else {
        ref.read(quizHistoryProvider.notifier).loadQuizHistory();
      }
    });
  }

  @override
  Widget build(BuildContext context) {
    final historyState = ref.watch(quizHistoryProvider);

    return Scaffold(
      appBar: AppBar(
        title: Text(
          widget.bookTitle != null
              ? 'Quiz History - ${widget.bookTitle}'
              : 'Quiz History',
        ),
        elevation: 0,
        actions: [
          IconButton(
            icon: const Icon(Icons.refresh),
            onPressed: () {
              if (widget.bookId != null) {
                ref
                    .read(quizHistoryProvider.notifier)
                    .loadQuizHistoryByBook(widget.bookId!);
              } else {
                ref.read(quizHistoryProvider.notifier).loadQuizHistory();
              }
            },
          ),
        ],
      ),
      body: historyState.isLoading
          ? const Center(child: CircularProgressIndicator())
          : historyState.error != null
              ? Center(
                  child: Column(
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: [
                      const Icon(Icons.error_outline,
                          size: 48, color: Colors.red),
                      const SizedBox(height: 16),
                      Text('Error: ${historyState.error}'),
                      const SizedBox(height: 16),
                      ElevatedButton(
                        onPressed: () {
                          if (widget.bookId != null) {
                            ref
                                .read(quizHistoryProvider.notifier)
                                .loadQuizHistoryByBook(widget.bookId!);
                          } else {
                            ref
                                .read(quizHistoryProvider.notifier)
                                .loadQuizHistory();
                          }
                        },
                        child: const Text('Retry'),
                      ),
                    ],
                  ),
                )
              : historyState.quizHistory.isEmpty
                  ? Center(
                      child: Column(
                        mainAxisAlignment: MainAxisAlignment.center,
                        children: [
                          const Icon(
                            Icons.quiz_outlined,
                            size: 64,
                            color: AppTheme.textHint,
                          ),
                          const SizedBox(height: 16),
                          Text(
                            'No quiz attempts yet',
                            style: Theme.of(context).textTheme.titleLarge,
                          ),
                          const SizedBox(height: 8),
                          Text(
                            'Take a quiz to see your history here',
                            style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                                  color: AppTheme.textSecondary,
                                ),
                          ),
                        ],
                      ),
                    )
                  : ListView.builder(
                      padding: const EdgeInsets.all(16),
                      itemCount: historyState.quizHistory.length,
                      itemBuilder: (context, index) {
                        final quiz = historyState.quizHistory[index];
                        return QuizHistoryCard(
                          quiz: quiz,
                          index: index,
                        );
                      },
                    ),
    );
  }
}

class QuizHistoryCard extends StatelessWidget {
  final QuizHistoryItem quiz;
  final int index;

  const QuizHistoryCard({
    required this.quiz,
    required this.index,
    super.key,
  });

  @override
  Widget build(BuildContext context) {
    final formattedDate = _formatDate(quiz.attemptedAt);
    final gradeColor = _getGradeColor(quiz.totalGrade);

    return Card(
      margin: const EdgeInsets.only(bottom: 12),
      elevation: 2,
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(16),
      ),
      child: Padding(
        padding: const EdgeInsets.all(0),
        child: Container(
          decoration: BoxDecoration(
            borderRadius: BorderRadius.circular(16),
            border: Border.all(
              color: gradeColor.withOpacity(0.3),
              width: 2,
            ),
          ),
          child: Material(
            color: Colors.transparent,
            child: InkWell(
              onTap: () {
                Navigator.push(
                  context,
                  MaterialPageRoute(
                    builder: (_) => QuizResultDetailScreen(quiz: quiz),
                  ),
                );
              },
              borderRadius: BorderRadius.circular(16),
              child: Padding(
                padding: const EdgeInsets.all(16),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Row(
                      mainAxisAlignment: MainAxisAlignment.spaceBetween,
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Expanded(
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              Text(
                                quiz.topicName,
                                style: Theme.of(context)
                                    .textTheme
                                    .titleMedium
                                    ?.copyWith(
                                      fontWeight: FontWeight.bold,
                                    ),
                                maxLines: 2,
                                overflow: TextOverflow.ellipsis,
                              ),
                              const SizedBox(height: 4),
                              Text(
                                formattedDate,
                                style: Theme.of(context)
                                    .textTheme
                                    .bodySmall
                                    ?.copyWith(
                                      color: AppTheme.textSecondary,
                                    ),
                              ),
                            ],
                          ),
                        ),
                        const SizedBox(width: 12),
                        // Grade badge
                        Container(
                          padding: const EdgeInsets.symmetric(
                            horizontal: 12,
                            vertical: 8,
                          ),
                          decoration: BoxDecoration(
                            color: gradeColor.withOpacity(0.1),
                            borderRadius: BorderRadius.circular(8),
                            border: Border.all(
                              color: gradeColor.withOpacity(0.3),
                            ),
                          ),
                          child: Column(
                            mainAxisSize: MainAxisSize.min,
                            children: [
                              Text(
                                quiz.totalGrade,
                                style: Theme.of(context)
                                    .textTheme
                                    .titleMedium
                                    ?.copyWith(
                                      color: gradeColor,
                                      fontWeight: FontWeight.bold,
                                    ),
                              ),
                              Text(
                                '${(quiz.totalScore * 100).toStringAsFixed(0)}%',
                                style: Theme.of(context)
                                    .textTheme
                                    .bodySmall
                                    ?.copyWith(color: gradeColor),
                              ),
                            ],
                          ),
                        ),
                      ],
                    ),
                    const SizedBox(height: 12),
                    // Score progress bar
                    ClipRRect(
                      borderRadius: BorderRadius.circular(8),
                      child: LinearProgressIndicator(
                        value: quiz.totalScore,
                        minHeight: 6,
                        backgroundColor: gradeColor.withOpacity(0.1),
                        valueColor: AlwaysStoppedAnimation<Color>(gradeColor),
                      ),
                    ),
                    const SizedBox(height: 12),
                    // Action button
                    SizedBox(
                      width: double.infinity,
                      child: ElevatedButton.icon(
                        icon: const Icon(Icons.refresh),
                        label: const Text('Retake Quiz'),
                        onPressed: () {
                          // TODO: Implement retake quiz functionality
                          ScaffoldMessenger.of(context).showSnackBar(
                            const SnackBar(
                              content: Text('Retaking quiz...'),
                            ),
                          );
                        },
                      ),
                    ),
                  ],
                ),
              ),
            ),
          ),
        ),
      ),
    );
  }

  Color _getGradeColor(String grade) {
    switch (grade) {
      case 'A':
      case 'A+':
        return AppTheme.successColor;
      case 'B':
      case 'B+':
        return const Color(0xFF3B82F6);
      case 'C':
      case 'C+':
        return AppTheme.warningColor;
      default:
        return AppTheme.errorColor;
    }
  }

  String _formatDate(String dateString) {
    try {
      final date = DateTime.parse(dateString);
      final now = DateTime.now();
      final diff = now.difference(date);

      if (diff.inDays == 0) {
        if (diff.inHours == 0) {
          return '${diff.inMinutes} minutes ago';
        }
        return '${diff.inHours} hours ago';
      } else if (diff.inDays == 1) {
        return 'Yesterday';
      } else if (diff.inDays < 7) {
        return '${diff.inDays} days ago';
      } else {
        return '${date.month}/${date.day}/${date.year}';
      }
    } catch (e) {
      return dateString;
    }
  }
}

class QuizResultDetailScreen extends StatelessWidget {
  final QuizHistoryItem quiz;

  const QuizResultDetailScreen({
    required this.quiz,
    super.key,
  });

  @override
  Widget build(BuildContext context) {
    final gradeColor = _getGradeColor(quiz.totalGrade);

    return Scaffold(
      appBar: AppBar(
        title: const Text('Quiz Result Details'),
        elevation: 0,
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            // Score card
            Card(
              elevation: 4,
              shape: RoundedRectangleBorder(
                borderRadius: BorderRadius.circular(16),
              ),
              child: Container(
                decoration: BoxDecoration(
                  borderRadius: BorderRadius.circular(16),
                  gradient: LinearGradient(
                    begin: Alignment.topLeft,
                    end: Alignment.bottomRight,
                    colors: [
                      gradeColor.withOpacity(0.8),
                      gradeColor.withOpacity(0.6),
                    ],
                  ),
                ),
                child: Padding(
                  padding: const EdgeInsets.all(24),
                  child: Column(
                    children: [
                      Text(
                        'Quiz Score',
                        style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                              color: Colors.white.withOpacity(0.7),
                            ),
                      ),
                      const SizedBox(height: 8),
                      Text(
                        quiz.totalGrade,
                        style:
                            Theme.of(context).textTheme.displayMedium?.copyWith(
                                  color: Colors.white,
                                  fontWeight: FontWeight.bold,
                                ),
                      ),
                      const SizedBox(height: 8),
                      Text(
                        '${(quiz.totalScore * 100).toStringAsFixed(0)}% Correct',
                        style:
                            Theme.of(context).textTheme.titleMedium?.copyWith(
                                  color: Colors.white,
                                ),
                      ),
                    ],
                  ),
                ),
              ),
            ),
            const SizedBox(height: 24),
            // Quiz info
            Container(
              padding: const EdgeInsets.all(16),
              decoration: BoxDecoration(
                color: AppTheme.backgroundColor,
                borderRadius: BorderRadius.circular(12),
              ),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  _buildInfoRow(
                    context,
                    'Topic',
                    quiz.topicName,
                  ),
                  const SizedBox(height: 12),
                  _buildInfoRow(
                    context,
                    'Attempted',
                    _formatDetailedDate(quiz.attemptedAt),
                  ),
                  const SizedBox(height: 12),
                  _buildInfoRow(
                    context,
                    'Score',
                    '${(quiz.totalScore * 100).toStringAsFixed(1)}%',
                  ),
                ],
              ),
            ),
            const SizedBox(height: 24),
            // Retake button
            ElevatedButton.icon(
              onPressed: () {
                // TODO: Implement retake quiz
                Navigator.pop(context);
              },
              icon: const Icon(Icons.refresh),
              label: const Text('Retake This Quiz'),
              style: ElevatedButton.styleFrom(
                padding: const EdgeInsets.symmetric(vertical: 16),
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildInfoRow(BuildContext context, String label, String value) {
    return Row(
      mainAxisAlignment: MainAxisAlignment.spaceBetween,
      children: [
        Text(
          label,
          style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                color: AppTheme.textSecondary,
              ),
        ),
        Text(
          value,
          style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                fontWeight: FontWeight.bold,
              ),
          maxLines: 2,
          overflow: TextOverflow.ellipsis,
        ),
      ],
    );
  }

  Color _getGradeColor(String grade) {
    switch (grade) {
      case 'A':
      case 'A+':
        return AppTheme.successColor;
      case 'B':
      case 'B+':
        return const Color(0xFF3B82F6);
      case 'C':
      case 'C+':
        return AppTheme.warningColor;
      default:
        return AppTheme.errorColor;
    }
  }

  String _formatDetailedDate(String dateString) {
    try {
      final date = DateTime.parse(dateString);
      return '${date.year}-${date.month.toString().padLeft(2, '0')}-${date.day.toString().padLeft(2, '0')} ${date.hour.toString().padLeft(2, '0')}:${date.minute.toString().padLeft(2, '0')}';
    } catch (e) {
      return dateString;
    }
  }
}

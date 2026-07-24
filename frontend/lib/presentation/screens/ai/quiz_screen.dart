import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import '../../providers/ai_quiz_provider.dart';
import '../../providers/book_provider.dart';
import '../../../core/theme/app_theme.dart';

class QuizScreen extends ConsumerStatefulWidget {
  final String bookId;

  const QuizScreen({super.key, required this.bookId});

  @override
  ConsumerState<QuizScreen> createState() => _QuizScreenState();
}

class _QuizScreenState extends ConsumerState<QuizScreen> {
  int _numQuestions = 5;
  String? _selectedTopicId; // null means "Whole Book"
  String? _selectedTopicTitle; // Track topic title for evaluation

  @override
  void initState() {
    super.initState();
    // Clear any existing quiz when entering
    WidgetsBinding.instance.addPostFrameCallback((_) {
      ref.read(aiQuizProvider.notifier).clearQuiz();
    });
  }

  Future<void> _generateQuiz() async {
    final success = await ref.read(aiQuizProvider.notifier).generateQuiz(
      bookId: _selectedTopicId == null ? widget.bookId : null,
      topicId: _selectedTopicId,
      topicName: _selectedTopicTitle, // Pass topic name
      numQuestions: _numQuestions,
    );

    if (success && mounted) {
      // Navigate to quiz taking screen
      context.push('/quiz/${widget.bookId}/take');
    } else if (!success && mounted) {
      // Show error message in SnackBar
      final errorMessage = ref.read(aiQuizProvider).error ?? 'Failed to generate quiz. Please try again.';
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text(errorMessage),
          backgroundColor: Colors.red,
          duration: const Duration(seconds: 5),
          action: SnackBarAction(
            label: 'OK',
            textColor: Colors.white,
            onPressed: () {},
          ),
        ),
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    final quizState = ref.watch(aiQuizProvider);
    final bookAsync = ref.watch(bookDetailProvider(widget.bookId));
    final topicsAsync = ref.watch(bookTopicsProvider(widget.bookId));

    return Scaffold(
      appBar: AppBar(
        title: const Text('Generate Quiz'),
      ),
      body: quizState.isLoading
          ? const Center(
              child: Column(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  CircularProgressIndicator(),
                  SizedBox(height: 16),
                  Text('Generating quiz questions...'),
                  SizedBox(height: 8),
                  Padding(
                    padding: EdgeInsets.symmetric(horizontal: 32),
                    child: Text(
                      'Using AI to create personalized questions from your book',
                      style: TextStyle(color: AppTheme.textSecondary),
                      textAlign: TextAlign.center,
                    ),
                  ),
                ],
              ),
            )
          : SingleChildScrollView(
              padding: const EdgeInsets.all(16),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.stretch,
                children: [
                  // Book info
                  bookAsync.when(
                    data: (book) => Card(
                      child: Padding(
                        padding: const EdgeInsets.all(16),
                        child: Column(
                          children: [
                            Container(
                              width: 80,
                              height: 100,
                              decoration: BoxDecoration(
                                color: AppTheme.primaryColor.withValues(alpha: 0.1),
                                borderRadius: BorderRadius.circular(8),
                              ),
                              child: const Icon(
                                Icons.menu_book,
                                size: 48,
                                color: AppTheme.primaryColor,
                              ),
                            ),
                            const SizedBox(height: 12),
                            Text(
                              book.title,
                              style: Theme.of(context).textTheme.titleLarge?.copyWith(
                                    fontWeight: FontWeight.bold,
                                  ),
                              textAlign: TextAlign.center,
                            ),
                          ],
                        ),
                      ),
                    ),
                    loading: () => const Card(
                      child: Padding(
                        padding: EdgeInsets.all(16),
                        child: Center(child: CircularProgressIndicator()),
                      ),
                    ),
                    error: (_, _) => const SizedBox.shrink(),
                  ),

                  const SizedBox(height: 24),

                  // Info card
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
                                Icons.auto_awesome,
                                color: AppTheme.primaryColor,
                              ),
                              const SizedBox(width: 8),
                              Text(
                                'AI-Powered Quiz',
                                style: Theme.of(context).textTheme.titleMedium?.copyWith(
                                      fontWeight: FontWeight.bold,
                                      color: AppTheme.primaryColor,
                                    ),
                              ),
                            ],
                          ),
                          const SizedBox(height: 8),
                          const Text(
                            'Test your knowledge with AI-generated questions based on the content of this book. Each quiz is personalized and focuses on key concepts.',
                          ),
                        ],
                      ),
                    ),
                  ),

                  const SizedBox(height: 24),

                  // Quiz settings
                  Text(
                    'Quiz Settings',
                    style: Theme.of(context).textTheme.titleMedium?.copyWith(
                          fontWeight: FontWeight.bold,
                        ),
                  ),
                  const SizedBox(height: 12),

                  // Topic selection
                  Card(
                    child: Padding(
                      padding: const EdgeInsets.all(16),
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Row(
                            children: [
                              const Icon(
                                Icons.book_outlined,
                                size: 20,
                                color: AppTheme.primaryColor,
                              ),
                              const SizedBox(width: 8),
                              Text(
                                'Select Chapter/Topic',
                                style: Theme.of(context).textTheme.titleSmall?.copyWith(
                                      fontWeight: FontWeight.w600,
                                    ),
                              ),
                            ],
                          ),
                          const SizedBox(height: 12),
                          topicsAsync.when(
                            data: (topics) {
                              if (topics.isEmpty) {
                                return Container(
                                  padding: const EdgeInsets.all(12),
                                  decoration: BoxDecoration(
                                    color: Colors.orange.shade50,
                                    borderRadius: BorderRadius.circular(8),
                                  ),
                                  child: const Row(
                                    children: [
                                      Icon(Icons.info_outline, color: Colors.orange),
                                      SizedBox(width: 8),
                                      Expanded(
                                        child: Text(
                                          'No topics found. Quiz will use the entire book content.',
                                          style: TextStyle(fontSize: 13),
                                        ),
                                      ),
                                    ],
                                  ),
                                );
                              }
                              return Column(
                                children: [
                                  // Whole book option
                                  RadioListTile<String?>(
                                    value: null,
                                    groupValue: _selectedTopicId,
                                    onChanged: (value) {
                                      setState(() {
                                        _selectedTopicId = value;
                                        _selectedTopicTitle = null;
                                      });
                                    },
                                    title: const Text(
                                      'Whole Book/PDF',
                                      style: TextStyle(fontWeight: FontWeight.w600),
                                    ),
                                    subtitle: const Text(
                                      'Generate quiz from random topics across the entire book',
                                      style: TextStyle(fontSize: 12),
                                    ),
                                    contentPadding: EdgeInsets.zero,
                                    dense: true,
                                  ),
                                  const Divider(),
                                  // Individual topics
                                  ...topics.map((topic) => RadioListTile<String?>(
                                        value: topic.id,
                                        groupValue: _selectedTopicId,
                                        onChanged: (value) {
                                          setState(() {
                                            _selectedTopicId = value;
                                            _selectedTopicTitle = topic.topicTitle;
                                          });
                                        },
                                        title: Text(
                                          topic.topicTitle,
                                          style: const TextStyle(fontSize: 14),
                                        ),
                                        subtitle: Text(
                                          'Page ${topic.pageStart}',
                                          style: const TextStyle(
                                            fontSize: 11,
                                            color: AppTheme.textSecondary,
                                          ),
                                        ),
                                        contentPadding: EdgeInsets.zero,
                                        dense: true,
                                      )),
                                ],
                              );
                            },
                            loading: () => const Center(
                              child: Padding(
                                padding: EdgeInsets.all(16),
                                child: CircularProgressIndicator(),
                              ),
                            ),
                            error: (error, _) => Container(
                              padding: const EdgeInsets.all(12),
                              decoration: BoxDecoration(
                                color: Colors.red.shade50,
                                borderRadius: BorderRadius.circular(8),
                              ),
                              child: Row(
                                children: [
                                  const Icon(Icons.error_outline, color: Colors.red),
                                  const SizedBox(width: 8),
                                  Expanded(
                                    child: Text(
                                      'Could not load topics: ${error.toString()}',
                                      style: const TextStyle(fontSize: 13),
                                    ),
                                  ),
                                ],
                              ),
                            ),
                          ),
                        ],
                      ),
                    ),
                  ),

                  const SizedBox(height: 16),

                  // Number of questions
                  Card(
                    child: Padding(
                      padding: const EdgeInsets.all(16),
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(
                            'Number of Questions: $_numQuestions',
                            style: Theme.of(context).textTheme.titleSmall,
                          ),
                          Slider(
                            value: _numQuestions.toDouble(),
                            min: 3,
                            max: 15,
                            divisions: 12,
                            label: '$_numQuestions questions',
                            onChanged: (value) {
                              setState(() {
                                _numQuestions = value.toInt();
                              });
                            },
                          ),
                          const SizedBox(height: 8),
                          Row(
                            mainAxisAlignment: MainAxisAlignment.spaceBetween,
                            children: [
                              TextButton(
                                onPressed: () => setState(() => _numQuestions = 3),
                                child: const Text('Quick (3)'),
                              ),
                              TextButton(
                                onPressed: () => setState(() => _numQuestions = 10),
                                child: const Text('Standard (10)'),
                              ),
                              TextButton(
                                onPressed: () => setState(() => _numQuestions = 15),
                                child: const Text('Deep (15)'),
                              ),
                            ],
                          ),
                        ],
                      ),
                    ),
                  ),

                  const SizedBox(height: 24),

                  // Features
                  Text(
                    'Quiz Features',
                    style: Theme.of(context).textTheme.titleMedium?.copyWith(
                          fontWeight: FontWeight.bold,
                        ),
                  ),
                  const SizedBox(height: 12),

                  _buildFeatureItem(
                    Icons.psychology,
                    'Smart Questions',
                    'AI analyzes your book to create relevant questions',
                  ),
                  _buildFeatureItem(
                    Icons.check_circle_outline,
                    'Multiple Choice',
                    'Each question has 4 options with one correct answer',
                  ),
                  _buildFeatureItem(
                    Icons.grade,
                    'Instant Results',
                    'Get immediate feedback and detailed scoring',
                  ),
                  _buildFeatureItem(
                    Icons.refresh,
                    'Unlimited Attempts',
                    'Take the quiz as many times as you want',
                  ),

                  const SizedBox(height: 24),

                  // Error message
                  if (quizState.error != null)
                    Container(
                      padding: const EdgeInsets.all(12),
                      decoration: BoxDecoration(
                        color: Colors.red.shade100,
                        borderRadius: BorderRadius.circular(8),
                      ),
                      child: Row(
                        children: [
                          const Icon(Icons.error_outline, color: Colors.red),
                          const SizedBox(width: 8),
                          Expanded(
                            child: Text(
                              quizState.error!,
                              style: const TextStyle(color: Colors.red),
                            ),
                          ),
                        ],
                      ),
                    ),

                  const SizedBox(height: 16),

                  // Generate button
                  ElevatedButton.icon(
                    onPressed: _generateQuiz,
                    icon: const Icon(Icons.play_arrow),
                    label: const Text('Start Quiz'),
                    style: ElevatedButton.styleFrom(
                      padding: const EdgeInsets.symmetric(vertical: 16),
                    ),
                  ),
                ],
              ),
            ),
    );
  }

  Widget _buildFeatureItem(IconData icon, String title, String description) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 12),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Icon(icon, color: AppTheme.primaryColor),
          const SizedBox(width: 12),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  title,
                  style: const TextStyle(fontWeight: FontWeight.bold),
                ),
                Text(
                  description,
                  style: const TextStyle(
                    color: AppTheme.textSecondary,
                    fontSize: 13,
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}

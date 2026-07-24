import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import '../../../core/theme/app_theme.dart';
import '../../providers/subject_profile_provider.dart';
import '../../../data/models/subject_profile_model.dart';

class DiagnosticQuizScreen extends ConsumerStatefulWidget {
  final String subject;

  const DiagnosticQuizScreen({super.key, required this.subject});

  @override
  ConsumerState<DiagnosticQuizScreen> createState() =>
      _DiagnosticQuizScreenState();
}

class _DiagnosticQuizScreenState extends ConsumerState<DiagnosticQuizScreen> {
  DiagnosticQuizResponse? _quiz;
  bool _isLoading = true;
  String? _error;
  List<String?> _selectedAnswers = [];
  int _currentQuestionIndex = 0;

  @override
  void initState() {
    super.initState();
    _loadQuiz();
  }

  Future<void> _loadQuiz() async {
    setState(() {
      _isLoading = true;
      _error = null;
    });

    try {
      final quiz =
          await ref.read(subjectProfileProvider.notifier).generateQuiz(widget.subject);

      if (quiz != null) {
        setState(() {
          _quiz = quiz;
          _selectedAnswers = List.filled(quiz.questions.length, null);
          _isLoading = false;
        });
      } else {
        setState(() {
          _error = ref.read(subjectProfileProvider).error ??
              'Failed to generate quiz';
          _isLoading = false;
        });
      }
    } catch (e) {
      setState(() {
        _error = e.toString();
        _isLoading = false;
      });
    }
  }

  void _selectAnswer(String answer) {
    setState(() {
      _selectedAnswers[_currentQuestionIndex] = answer;
    });
  }

  void _nextQuestion() {
    if (_currentQuestionIndex < (_quiz?.questions.length ?? 0) - 1) {
      setState(() {
        _currentQuestionIndex++;
      });
    }
  }

  void _previousQuestion() {
    if (_currentQuestionIndex > 0) {
      setState(() {
        _currentQuestionIndex--;
      });
    }
  }

  bool get _allQuestionsAnswered {
    return _selectedAnswers.every((answer) => answer != null);
  }

  Future<void> _submitQuiz() async {
    if (!_allQuestionsAnswered) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text('Please answer all questions'),
          backgroundColor: AppTheme.errorColor,
        ),
      );
      return;
    }

    // Show loading dialog
    if (mounted) {
      showDialog(
        context: context,
        barrierDismissible: false,
        builder: (context) => const Center(
          child: Card(
            child: Padding(
              padding: EdgeInsets.all(24),
              child: Column(
                mainAxisSize: MainAxisSize.min,
                children: [
                  CircularProgressIndicator(),
                  SizedBox(height: 16),
                  Text('Analyzing your answers...'),
                ],
              ),
            ),
          ),
        ),
      );
    }

    final success = await ref.read(subjectProfileProvider.notifier).submitQuizAnswers(
          subject: widget.subject,
          answers: _selectedAnswers.cast<String>(),
        );

    if (mounted) {
      // Close loading dialog safely
      if (Navigator.of(context).canPop()) {
        Navigator.of(context).pop();
      }

      if (success) {
        context.go('/preferences');
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('${widget.subject} profile created successfully!'),
            backgroundColor: Colors.green,
          ),
        );
      } else {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text(
                ref.read(subjectProfileProvider).error ?? 'Failed to submit quiz'),
            backgroundColor: AppTheme.errorColor,
          ),
        );
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text('Diagnostic Quiz: ${widget.subject}'),
        leading: IconButton(
          icon: const Icon(Icons.close),
          onPressed: () => context.pop(),
        ),
      ),
      body: _isLoading
          ? const Center(child: CircularProgressIndicator())
          : _error != null
              ? _buildErrorState()
              : _quiz == null
                  ? const Center(child: Text('No quiz available'))
                  : _buildQuizContent(),
    );
  }

  Widget _buildErrorState() {
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(24),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            const Icon(
              Icons.error_outline,
              size: 64,
              color: AppTheme.errorColor,
            ),
            const SizedBox(height: 16),
            Text(
              'Failed to Load Quiz',
              style: Theme.of(context).textTheme.titleLarge,
            ),
            const SizedBox(height: 8),
            Text(
              _error ?? 'Unknown error',
              textAlign: TextAlign.center,
              style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                    color: AppTheme.textSecondary,
                  ),
            ),
            const SizedBox(height: 24),
            ElevatedButton.icon(
              onPressed: _loadQuiz,
              icon: const Icon(Icons.refresh),
              label: const Text('Retry'),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildQuizContent() {
    final question = _quiz!.questions[_currentQuestionIndex];
    final progress = (_currentQuestionIndex + 1) / _quiz!.questions.length;

    return Column(
      children: [
        // Progress indicator
        LinearProgressIndicator(
          value: progress,
          backgroundColor: AppTheme.primaryColor.withValues(alpha: 0.2),
        ),
        
        Expanded(
          child: SingleChildScrollView(
            padding: const EdgeInsets.all(24),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                // Question counter
                Text(
                  'Question ${_currentQuestionIndex + 1} of ${_quiz!.questions.length}',
                  style: Theme.of(context).textTheme.labelLarge?.copyWith(
                        color: AppTheme.primaryColor,
                      ),
                ),
                const SizedBox(height: 16),

                // Question text
                Text(
                  question.question,
                  style: Theme.of(context).textTheme.headlineSmall?.copyWith(
                        fontWeight: FontWeight.bold,
                      ),
                ),
                const SizedBox(height: 32),

                // Options
                ...question.options.asMap().entries.map((entry) {
                  final index = entry.key;
                  final option = entry.value;
                  final isSelected = _selectedAnswers[_currentQuestionIndex] == option;

                  return Padding(
                    padding: const EdgeInsets.only(bottom: 12),
                    child: InkWell(
                      onTap: () => _selectAnswer(option),
                      borderRadius: BorderRadius.circular(12),
                      child: Container(
                        padding: const EdgeInsets.all(16),
                        decoration: BoxDecoration(
                          color: isSelected
                              ? AppTheme.primaryColor.withValues(alpha: 0.1)
                              : Colors.transparent,
                          border: Border.all(
                            color: isSelected
                                ? AppTheme.primaryColor
                                : AppTheme.textSecondary.withValues(alpha: 0.3),
                            width: isSelected ? 2 : 1,
                          ),
                          borderRadius: BorderRadius.circular(12),
                        ),
                        child: Row(
                          children: [
                            Container(
                              width: 32,
                              height: 32,
                              decoration: BoxDecoration(
                                shape: BoxShape.circle,
                                color: isSelected
                                    ? AppTheme.primaryColor
                                    : Colors.transparent,
                                border: Border.all(
                                  color: isSelected
                                      ? AppTheme.primaryColor
                                      : AppTheme.textSecondary.withValues(alpha: 0.5),
                                ),
                              ),
                              child: Center(
                                child: Text(
                                  String.fromCharCode(65 + index), // A, B, C, D
                                  style: TextStyle(
                                    fontWeight: FontWeight.bold,
                                    color: isSelected ? Colors.white : AppTheme.textSecondary,
                                  ),
                                ),
                              ),
                            ),
                            const SizedBox(width: 16),
                            Expanded(
                              child: Text(
                                option,
                                style: Theme.of(context).textTheme.bodyLarge?.copyWith(
                                      color: isSelected
                                          ? AppTheme.textPrimary
                                          : AppTheme.textSecondary,
                                      fontWeight: isSelected ? FontWeight.w600 : FontWeight.normal,
                                    ),
                              ),
                            ),
                          ],
                        ),
                      ),
                    ),
                  );
                }),
              ],
            ),
          ),
        ),

        // Navigation buttons
        Container(
          padding: const EdgeInsets.all(16),
          decoration: BoxDecoration(
            color: Colors.white,
            boxShadow: [
              BoxShadow(
                color: Colors.black.withValues(alpha: 0.05),
                blurRadius: 10,
                offset: const Offset(0, -2),
              ),
            ],
          ),
          child: Row(
            children: [
              if (_currentQuestionIndex > 0)
                Expanded(
                  child: OutlinedButton.icon(
                    onPressed: _previousQuestion,
                    icon: const Icon(Icons.arrow_back),
                    label: const Text('Previous'),
                  ),
                ),
              if (_currentQuestionIndex > 0) const SizedBox(width: 12),
              Expanded(
                flex: 2,
                child: _currentQuestionIndex < _quiz!.questions.length - 1
                    ? ElevatedButton.icon(
                        onPressed: _selectedAnswers[_currentQuestionIndex] != null
                            ? _nextQuestion
                            : null,
                        icon: const Icon(Icons.arrow_forward),
                        label: const Text('Next'),
                      )
                    : ElevatedButton.icon(
                        onPressed: _allQuestionsAnswered ? _submitQuiz : null,
                        icon: const Icon(Icons.check),
                        label: const Text('Submit Quiz'),
                      ),
              ),
            ],
          ),
        ),
      ],
    );
  }
}

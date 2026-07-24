import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../providers/ai_study_tools_provider.dart';
import '../../../data/models/ai_model.dart';
import '../../../core/theme/app_theme.dart';
import '../../../data/models/book_model.dart';
import '../../providers/book_provider.dart';
import '../../../core/providers/app_providers.dart';

class FlashcardsScreen extends ConsumerStatefulWidget {
  const FlashcardsScreen({super.key});

  @override
  ConsumerState<FlashcardsScreen> createState() => _FlashcardsScreenState();
}

class _FlashcardsScreenState extends ConsumerState<FlashcardsScreen> {
  final TextEditingController _textController = TextEditingController();
  final PageController _flashcardController = PageController();
  int _currentCardIndex = 0;
  bool _showAnswer = false;
  bool _showInput = true;
  String? _selectedBookId;
  String? _selectedTopicId;
  List<BookTopicModel> _topics = [];
  bool _isLoadingTopics = false;
  bool _useCustomText = false;

  @override
  void initState() {
    super.initState();
    // Fetch books when screen loads
    WidgetsBinding.instance.addPostFrameCallback((_) {
      ref.read(bookProvider.notifier).fetchBooks();
    });
  }

  @override
  void dispose() {
    _textController.dispose();
    _flashcardController.dispose();
    super.dispose();
  }

  Future<void> _loadTopicsForBook(String bookId) async {
    setState(() {
      _isLoadingTopics = true;
      _selectedTopicId = null;
      _topics = [];
    });

    final bookService = ref.read(bookApiServiceProvider);
    final result = await bookService.getBookTopics(bookId);

    result.when(
      success: (topics) {
        if (mounted) {
          setState(() {
            _topics = topics;
            _isLoadingTopics = false;
          });
        }
      },
      failure: (error) {
        if (mounted) {
          setState(() {
            _isLoadingTopics = false;
          });
          ScaffoldMessenger.of(context).showSnackBar(
            SnackBar(content: Text('Failed to load topics: $error')),
          );
        }
      },
    );
  }

  Future<void> _generateFlashcards() async {
    String textToProcess = '';

    if (_useCustomText) {
      // Use custom text from text field
      textToProcess = _textController.text.trim();
      if (textToProcess.isEmpty) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('Please enter some text to generate flashcards')),
        );
        return;
      }
    } else {
      // Fetch text from selected book/topic
      if (_selectedBookId == null) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('Please select a book')),
        );
        return;
      }

      final bookService = ref.read(bookApiServiceProvider);

      if (_selectedTopicId != null) {
        // Fetch specific topic text
        final result = await bookService.getTopicText(_selectedBookId!, _selectedTopicId!);
        result.when(
          success: (content) {
            textToProcess = content;
          },
          failure: (error) {
            ScaffoldMessenger.of(context).showSnackBar(
              SnackBar(content: Text('Failed to fetch topic text: $error')),
            );
            return;
          },
        );
      } else {
        // Fetch whole book text
        final result = await bookService.getBookExtractedText(_selectedBookId!);
        result.when(
          success: (bookText) {
            textToProcess = bookText.content;
          },
          failure: (error) {
            ScaffoldMessenger.of(context).showSnackBar(
              SnackBar(content: Text('Failed to fetch book text: $error')),
            );
            return;
          },
        );
      }
    }

    if (textToProcess.isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('No text available to generate flashcards')),
      );
      return;
    }

    await ref.read(studyToolsProvider.notifier).generateFlashcards(textToProcess);
    
    if (ref.read(studyToolsProvider).flashcards.isNotEmpty) {
      setState(() {
        _showInput = false;
        _currentCardIndex = 0;
        _showAnswer = false;
      });
    }
  }

  void _nextCard() {
    final flashcards = ref.read(studyToolsProvider).flashcards;
    if (_currentCardIndex < flashcards.length - 1) {
      _flashcardController.nextPage(
        duration: const Duration(milliseconds: 300),
        curve: Curves.easeInOut,
      );
      setState(() {
        _currentCardIndex++;
        _showAnswer = false;
      });
    }
  }

  void _previousCard() {
    if (_currentCardIndex > 0) {
      _flashcardController.previousPage(
        duration: const Duration(milliseconds: 300),
        curve: Curves.easeInOut,
      );
      setState(() {
        _currentCardIndex--;
        _showAnswer = false;
      });
    }
  }

  void _flipCard() {
    setState(() {
      _showAnswer = !_showAnswer;
    });
  }

  @override
  Widget build(BuildContext context) {
    final studyToolsState = ref.watch(studyToolsProvider);

    return Scaffold(
      appBar: AppBar(
        title: const Text('Flashcards'),
        actions: [
          if (studyToolsState.flashcards.isNotEmpty && !_showInput)
            IconButton(
              icon: const Icon(Icons.refresh),
              onPressed: () {
                ref.read(studyToolsProvider.notifier).clearFlashcards();
                setState(() {
                  _showInput = true;
                  _currentCardIndex = 0;
                  _showAnswer = false;
                  _selectedBookId = null;
                  _selectedTopicId = null;
                  _topics = [];
                  _useCustomText = false;
                });
              },
              tooltip: 'New flashcards',
            ),
        ],
      ),
      body: Column(
        children: [
          // Error banner
          if (studyToolsState.error != null)
            Container(
              width: double.infinity,
              padding: const EdgeInsets.all(12),
              color: Colors.red.shade100,
              child: Row(
                children: [
                  const Icon(Icons.error_outline, color: Colors.red),
                  const SizedBox(width: 8),
                  Expanded(
                    child: Text(
                      studyToolsState.error!,
                      style: const TextStyle(color: Colors.red),
                    ),
                  ),
                  IconButton(
                    icon: const Icon(Icons.close, color: Colors.red),
                    onPressed: () {
                      ref.read(studyToolsProvider.notifier).clearError();
                    },
                  ),
                ],
              ),
            ),

          // Main content
          Expanded(
            child: studyToolsState.isLoadingFlashcards
                ? const Center(
                    child: Column(
                      mainAxisAlignment: MainAxisAlignment.center,
                      children: [
                        CircularProgressIndicator(),
                        SizedBox(height: 16),
                        Text('Generating flashcards...'),
                        SizedBox(height: 8),
                        Padding(
                          padding: EdgeInsets.symmetric(horizontal: 32),
                          child: Text(
                            'Creating study materials from your text',
                            style: TextStyle(color: AppTheme.textSecondary),
                            textAlign: TextAlign.center,
                          ),
                        ),
                      ],
                    ),
                  )
                : studyToolsState.flashcards.isNotEmpty && !_showInput
                    ? _buildFlashcardsView(studyToolsState.flashcards)
                    : _buildInputView(),
          ),
        ],
      ),
      floatingActionButton: _showInput && !studyToolsState.isLoadingFlashcards
          ? FloatingActionButton.extended(
              onPressed: _generateFlashcards,
              icon: const Icon(Icons.auto_awesome),
              label: const Text('Generate'),
            )
          : null,
    );
  }

  Widget _buildInputView() {
    final bookState = ref.watch(bookProvider);

    return SingleChildScrollView(
      padding: const EdgeInsets.all(16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          Card(
            child: Padding(
              padding: const EdgeInsets.all(16),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(
                    children: [
                      const Icon(
                        Icons.info_outline,
                        color: AppTheme.primaryColor,
                        size: 20,
                      ),
                      const SizedBox(width: 8),
                      Text(
                        'Create Study Flashcards',
                        style: Theme.of(context).textTheme.titleMedium?.copyWith(
                              fontWeight: FontWeight.bold,
                            ),
                      ),
                    ],
                  ),
                  const SizedBox(height: 8),
                  const Text(
                    'Select a book and topic, or paste custom text. AI will create question-answer flashcards to help you study.',
                  ),
                ],
              ),
            ),
          ),
          const SizedBox(height: 16),

          // Toggle between book selection and custom text
          SegmentedButton<bool>(
            segments: const [
              ButtonSegment(
                value: false,
                label: Text('From Book'),
                icon: Icon(Icons.menu_book, size: 18),
              ),
              ButtonSegment(
                value: true,
                label: Text('Custom Text'),
                icon: Icon(Icons.edit, size: 18),
              ),
            ],
            selected: {_useCustomText},
            onSelectionChanged: (Set<bool> newSelection) {
              setState(() {
                _useCustomText = newSelection.first;
                _selectedBookId = null;
                _selectedTopicId = null;
                _topics = [];
              });
            },
          ),
          const SizedBox(height: 16),

          if (!_useCustomText) ...[
            // Book selection dropdown
            Text(
              'Select Book',
              style: Theme.of(context).textTheme.titleMedium?.copyWith(
                    fontWeight: FontWeight.bold,
                  ),
            ),
            const SizedBox(height: 8),
            if (bookState.isLoading)
              const Center(child: CircularProgressIndicator())
            else if (bookState.error != null)
              Card(
                child: Padding(
                  padding: const EdgeInsets.all(16),
                  child: Text('Failed to load books: ${bookState.error}'),
                ),
              )
            else ...[
              () {
                final completedBooks = bookState.books.where((b) => b.isCompleted).toList();
                if (completedBooks.isEmpty) {
                  return const Card(
                    child: Padding(
                      padding: EdgeInsets.all(16),
                      child: Text('No books available. Please upload a book first.'),
                    ),
                  );
                }
                return DropdownButtonFormField<String>(
                  initialValue: _selectedBookId,
                  decoration: InputDecoration(
                    border: OutlineInputBorder(
                      borderRadius: BorderRadius.circular(12),
                    ),
                    filled: true,
                    prefixIcon: const Icon(Icons.menu_book),
                  ),
                  hint: const Text('Choose a book'),
                  items: completedBooks.map((book) {
                    return DropdownMenuItem(
                      value: book.id,
                      child: Text(
                        book.title,
                        overflow: TextOverflow.ellipsis,
                      ),
                    );
                  }).toList(),
                  onChanged: (String? newValue) {
                    setState(() {
                      _selectedBookId = newValue;
                      _selectedTopicId = null;
                    });
                    if (newValue != null) {
                      _loadTopicsForBook(newValue);
                    }
                  },
                );
              }(),
            ],
            const SizedBox(height: 16),

            // Topic selection dropdown (only if book selected)
            if (_selectedBookId != null) ...[
              Text(
                'Select Topic (Optional)',
                style: Theme.of(context).textTheme.titleMedium?.copyWith(
                      fontWeight: FontWeight.bold,
                    ),
              ),
              const SizedBox(height: 8),
              if (_isLoadingTopics)
                const Center(child: CircularProgressIndicator())
              else if (_topics.isEmpty)
                const Card(
                  child: Padding(
                    padding: EdgeInsets.all(16),
                    child: Text('No topics found. Will use entire book.'),
                  ),
                )
              else
                DropdownButtonFormField<String>(
                  initialValue: _selectedTopicId,
                  decoration: InputDecoration(
                    border: OutlineInputBorder(
                      borderRadius: BorderRadius.circular(12),
                    ),
                    filled: true,
                    prefixIcon: const Icon(Icons.topic),
                  ),
                  hint: const Text('Choose a topic (or leave empty for full book)'),
                  items: _topics.map((topic) {
                    return DropdownMenuItem(
                      value: topic.id,
                      child: Text(
                        topic.topicTitle,
                        overflow: TextOverflow.ellipsis,
                      ),
                    );
                  }).toList(),
                  onChanged: (String? newValue) {
                    setState(() {
                      _selectedTopicId = newValue;
                    });
                  },
                ),
              const SizedBox(height: 16),
            ],
          ] else ...[
            // Custom text input
            Text(
              'Enter Study Material',
              style: Theme.of(context).textTheme.titleMedium?.copyWith(
                    fontWeight: FontWeight.bold,
                  ),
            ),
            const SizedBox(height: 8),
            TextField(
              controller: _textController,
              decoration: InputDecoration(
                hintText: 'Paste your study material here...\n\nInclude key concepts, definitions, or important information you want to memorize.',
                border: OutlineInputBorder(
                  borderRadius: BorderRadius.circular(12),
                ),
                filled: true,
              ),
              maxLines: 15,
              minLines: 10,
            ),
          ],
          const SizedBox(height: 80), // Space for FAB
        ],
      ),
    );
  }

  Widget _buildFlashcardsView(List<FlashcardModel> flashcards) {
    return Column(
      children: [
        // Progress indicator
        Container(
          padding: const EdgeInsets.all(16),
          child: Column(
            children: [
              Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  Text(
                    'Card ${_currentCardIndex + 1} of ${flashcards.length}',
                    style: Theme.of(context).textTheme.titleMedium?.copyWith(
                          fontWeight: FontWeight.bold,
                        ),
                  ),
                  Text(
                    '${(((_currentCardIndex + 1) / flashcards.length) * 100).toInt()}%',
                    style: Theme.of(context).textTheme.titleMedium?.copyWith(
                          color: AppTheme.primaryColor,
                          fontWeight: FontWeight.bold,
                        ),
                  ),
                ],
              ),
              const SizedBox(height: 8),
              LinearProgressIndicator(
                value: (_currentCardIndex + 1) / flashcards.length,
                backgroundColor: Colors.grey.shade200,
                valueColor: const AlwaysStoppedAnimation<Color>(AppTheme.primaryColor),
              ),
            ],
          ),
        ),

        // Flashcard
        Expanded(
          child: PageView.builder(
            controller: _flashcardController,
            physics: const NeverScrollableScrollPhysics(),
            itemCount: flashcards.length,
            onPageChanged: (index) {
              setState(() {
                _currentCardIndex = index;
                _showAnswer = false;
              });
            },
            itemBuilder: (context, index) {
              return _buildFlashcard(flashcards[index]);
            },
          ),
        ),

        // Navigation controls
        Container(
          padding: const EdgeInsets.all(16),
          child: Column(
            children: [
              // Flip button
              SizedBox(
                width: double.infinity,
                child: ElevatedButton.icon(
                  onPressed: _flipCard,
                  icon: Icon(_showAnswer ? Icons.visibility_off : Icons.visibility),
                  label: Text(_showAnswer ? 'Hide Answer' : 'Show Answer'),
                  style: ElevatedButton.styleFrom(
                    padding: const EdgeInsets.symmetric(vertical: 16),
                  ),
                ),
              ),
              const SizedBox(height: 12),
              // Previous/Next buttons
              Row(
                children: [
                  Expanded(
                    child: OutlinedButton.icon(
                      onPressed: _currentCardIndex > 0 ? _previousCard : null,
                      icon: const Icon(Icons.arrow_back),
                      label: const Text('Previous'),
                    ),
                  ),
                  const SizedBox(width: 12),
                  Expanded(
                    child: ElevatedButton.icon(
                      onPressed: _currentCardIndex < flashcards.length - 1
                          ? _nextCard
                          : null,
                      icon: const Icon(Icons.arrow_forward),
                      label: const Text('Next'),
                    ),
                  ),
                ],
              ),
            ],
          ),
        ),
      ],
    );
  }

  Widget _buildFlashcard(FlashcardModel flashcard) {
    return Padding(
      padding: const EdgeInsets.all(16),
      child: GestureDetector(
        onTap: _flipCard,
        child: Card(
          elevation: 8,
          child: Container(
            padding: const EdgeInsets.all(24),
            child: Column(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                // Question/Answer indicator
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
                  decoration: BoxDecoration(
                    color: _showAnswer
                        ? Colors.green.withValues(alpha: 0.1)
                        : AppTheme.primaryColor.withValues(alpha: 0.1),
                    borderRadius: BorderRadius.circular(20),
                  ),
                  child: Row(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      Icon(
                        _showAnswer ? Icons.lightbulb : Icons.help_outline,
                        size: 20,
                        color: _showAnswer ? Colors.green : AppTheme.primaryColor,
                      ),
                      const SizedBox(width: 8),
                      Text(
                        _showAnswer ? 'Answer' : 'Question',
                        style: TextStyle(
                          color: _showAnswer ? Colors.green : AppTheme.primaryColor,
                          fontWeight: FontWeight.bold,
                        ),
                      ),
                    ],
                  ),
                ),
                const SizedBox(height: 24),

                // Content
                Expanded(
                  child: Center(
                    child: SingleChildScrollView(
                      child: Text(
                        _showAnswer ? flashcard.answer : flashcard.question,
                        style: Theme.of(context).textTheme.headlineSmall?.copyWith(
                              height: 1.5,
                            ),
                        textAlign: TextAlign.center,
                      ),
                    ),
                  ),
                ),

                const SizedBox(height: 16),

                // Tap to flip hint
                Text(
                  'Tap card to ${_showAnswer ? "hide" : "reveal"} answer',
                  style: Theme.of(context).textTheme.bodySmall?.copyWith(
                        color: AppTheme.textSecondary,
                        fontStyle: FontStyle.italic,
                      ),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}

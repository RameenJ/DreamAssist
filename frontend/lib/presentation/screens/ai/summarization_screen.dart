import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../providers/ai_study_tools_provider.dart';
import '../../providers/book_provider.dart';
import '../../../core/theme/app_theme.dart';
import '../../../data/models/book_model.dart';
import '../../../core/providers/app_providers.dart';

class SummarizationScreen extends ConsumerStatefulWidget {
  final String? bookId;

  const SummarizationScreen({super.key, this.bookId});

  @override
  ConsumerState<SummarizationScreen> createState() => _SummarizationScreenState();
}

class _SummarizationScreenState extends ConsumerState<SummarizationScreen> {
  final TextEditingController _textController = TextEditingController();
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

  Future<void> _summarizeText() async {
    String textToSummarize = '';

    if (_useCustomText) {
      // Use custom text from text field
      textToSummarize = _textController.text.trim();
      if (textToSummarize.isEmpty) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('Please enter some text to summarize')),
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
            textToSummarize = content;
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
            textToSummarize = bookText.content;
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

    if (textToSummarize.isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('No text available to summarize')),
      );
      return;
    }

    await ref.read(studyToolsProvider.notifier).summarizeText(textToSummarize);
    setState(() => _showInput = false);
  }

  void _copyToClipboard(String text) {
    Clipboard.setData(ClipboardData(text: text));
    ScaffoldMessenger.of(context).showSnackBar(
      const SnackBar(content: Text('Summary copied to clipboard')),
    );
  }

  @override
  Widget build(BuildContext context) {
    final studyToolsState = ref.watch(studyToolsProvider);
    final bookAsync = widget.bookId != null
        ? ref.watch(bookDetailProvider(widget.bookId!))
        : null;

    return Scaffold(
      appBar: AppBar(
        title: const Text('Text Summarization'),
        actions: [
          if (studyToolsState.summary != null)
            IconButton(
              icon: const Icon(Icons.refresh),
              onPressed: () {
                ref.read(studyToolsProvider.notifier).clearSummary();
                setState(() {
                  _showInput = true;
                  _selectedBookId = null;
                  _selectedTopicId = null;
                  _topics = [];
                  _useCustomText = false;
                });
              },
              tooltip: 'New summary',
            ),
        ],
      ),
      body: Column(
        children: [
          // Book info banner
          if (bookAsync != null)
            bookAsync.when(
              data: (book) => Container(
                width: double.infinity,
                padding: const EdgeInsets.all(12),
                color: AppTheme.primaryColor.withValues(alpha: 0.1),
                child: Row(
                  children: [
                    const Icon(Icons.menu_book, color: AppTheme.primaryColor),
                    const SizedBox(width: 8),
                    Expanded(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(
                            'Summarizing from:',
                            style: Theme.of(context).textTheme.bodySmall,
                          ),
                          Text(
                            book.title,
                            style: const TextStyle(
                              fontWeight: FontWeight.bold,
                              color: AppTheme.primaryColor,
                            ),
                          ),
                        ],
                      ),
                    ),
                  ],
                ),
              ),
              loading: () => const SizedBox.shrink(),
              error: (_, _) => const SizedBox.shrink(),
            ),

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
            child: studyToolsState.isLoadingSummary
                ? const Center(
                    child: Column(
                      mainAxisAlignment: MainAxisAlignment.center,
                      children: [
                        CircularProgressIndicator(),
                        SizedBox(height: 16),
                        Text('Generating summary...'),
                        SizedBox(height: 8),
                        Padding(
                          padding: EdgeInsets.symmetric(horizontal: 32),
                          child: Text(
                            'This may take a moment',
                            style: TextStyle(color: AppTheme.textSecondary),
                            textAlign: TextAlign.center,
                          ),
                        ),
                      ],
                    ),
                  )
                : studyToolsState.summary != null && !_showInput
                    ? _buildSummaryView(studyToolsState.summary!)
                    : _buildInputView(),
          ),
        ],
      ),
      floatingActionButton: _showInput && !studyToolsState.isLoadingSummary
          ? FloatingActionButton.extended(
              onPressed: _summarizeText,
              icon: const Icon(Icons.auto_awesome),
              label: const Text('Summarize'),
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
                        'How it works',
                        style: Theme.of(context).textTheme.titleMedium?.copyWith(
                              fontWeight: FontWeight.bold,
                            ),
                      ),
                    ],
                  ),
                  const SizedBox(height: 8),
                  const Text(
                    'Select a book and topic, or paste custom text. Our AI will generate a concise summary highlighting the key points.',
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
                    child: Text('No topics found. Will summarize entire book.'),
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
              'Enter Text to Summarize',
              style: Theme.of(context).textTheme.titleMedium?.copyWith(
                    fontWeight: FontWeight.bold,
                  ),
            ),
            const SizedBox(height: 8),
            TextField(
              controller: _textController,
              decoration: InputDecoration(
                hintText: 'Paste your text here...\n\nYou can summarize chapters, articles, notes, or any long-form content.',
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

  Widget _buildSummaryView(String summary) {
    return SingleChildScrollView(
      padding: const EdgeInsets.all(16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          // Summary card
          Card(
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
                        'AI Summary',
                        style: Theme.of(context).textTheme.titleLarge?.copyWith(
                              fontWeight: FontWeight.bold,
                            ),
                      ),
                      const Spacer(),
                      IconButton(
                        icon: const Icon(Icons.copy),
                        onPressed: () => _copyToClipboard(summary),
                        tooltip: 'Copy summary',
                      ),
                    ],
                  ),
                  const Divider(height: 24),
                  Text(
                    summary,
                    style: Theme.of(context).textTheme.bodyLarge?.copyWith(
                          height: 1.6,
                        ),
                  ),
                ],
              ),
            ),
          ),

          const SizedBox(height: 16),

          // Original text card (if available)
          if (_textController.text.isNotEmpty)
            ExpansionTile(
              title: const Text('View Original Text'),
              leading: const Icon(Icons.text_snippet),
              children: [
                Padding(
                  padding: const EdgeInsets.all(16),
                  child: Text(
                    _textController.text,
                    style: const TextStyle(color: AppTheme.textSecondary),
                  ),
                ),
              ],
            ),

          const SizedBox(height: 16),

          // Actions
          Row(
            children: [
              Expanded(
                child: OutlinedButton.icon(
                  onPressed: () {
                    ref.read(studyToolsProvider.notifier).clearSummary();
                    setState(() => _showInput = true);
                  },
                  icon: const Icon(Icons.refresh),
                  label: const Text('New Summary'),
                ),
              ),
              const SizedBox(width: 8),
              Expanded(
                child: ElevatedButton.icon(
                  onPressed: () => _copyToClipboard(summary),
                  icon: const Icon(Icons.copy),
                  label: const Text('Copy'),
                ),
              ),
            ],
          ),
        ],
      ),
    );
  }
}

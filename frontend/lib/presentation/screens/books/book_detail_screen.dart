import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import '../../providers/book_provider.dart';
import '../../../core/theme/app_theme.dart';
import '../ai/flashcard_history_screen.dart';
import '../ai/quiz_history_screen.dart';

class BookDetailScreen extends ConsumerStatefulWidget {
  final String bookId;

  const BookDetailScreen({super.key, required this.bookId});

  @override
  ConsumerState<BookDetailScreen> createState() => _BookDetailScreenState();
}

class _BookDetailScreenState extends ConsumerState<BookDetailScreen> {
  Future<void> _showDeleteConfirmation(BuildContext context, String bookTitle) async {
    final confirmed = await showDialog<bool>(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Delete Book'),
        content: Text(
          'Are you sure you want to delete "$bookTitle"?\n\nThis will remove the book and all associated data (PDF, extracted text, AI data). This action cannot be undone.',
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.of(context).pop(false),
            child: const Text('Cancel'),
          ),
          TextButton(
            onPressed: () => Navigator.of(context).pop(true),
            style: TextButton.styleFrom(foregroundColor: AppTheme.errorColor),
            child: const Text('Delete'),
          ),
        ],
      ),
    );

    if (confirmed == true && context.mounted) {
      // Show loading indicator
      showDialog(
        context: context,
        barrierDismissible: false,
        builder: (context) => const Center(child: CircularProgressIndicator()),
      );

      // Delete the book
      final success = await ref.read(bookProvider.notifier).deleteBook(widget.bookId);

      if (context.mounted) {
        // Close loading dialog
        Navigator.of(context).pop();

        if (success) {
          // Show success message
          ScaffoldMessenger.of(context).showSnackBar(
            const SnackBar(
              content: Text('Book deleted successfully'),
              backgroundColor: AppTheme.successColor,
            ),
          );
          // Go back to books list
          context.pop();
        } else {
          // Show error message
          ScaffoldMessenger.of(context).showSnackBar(
            const SnackBar(
              content: Text('Failed to delete book. Please try again.'),
              backgroundColor: AppTheme.errorColor,
            ),
          );
        }
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    final bookAsync = ref.watch(bookDetailProvider(widget.bookId));

    return Scaffold(
      appBar: AppBar(
        title: const Text('Book Details'),
      ),
      body: bookAsync.when(
        data: (book) => SingleChildScrollView(
          padding: const EdgeInsets.all(16),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              // Book header
              Card(
                child: Padding(
                  padding: const EdgeInsets.all(16),
                  child: Column(
                    children: [
                      Container(
                        width: 120,
                        height: 160,
                        decoration: BoxDecoration(
                          color: AppTheme.primaryColor.withValues(alpha: 0.1),
                          borderRadius: BorderRadius.circular(12),
                        ),
                        child: const Icon(
                          Icons.menu_book,
                          size: 64,
                          color: AppTheme.primaryColor,
                        ),
                      ),
                      const SizedBox(height: 16),
                      Text(
                        book.title,
                        style: Theme.of(context).textTheme.headlineSmall?.copyWith(
                              fontWeight: FontWeight.bold,
                            ),
                        textAlign: TextAlign.center,
                      ),
                      const SizedBox(height: 8),
                      if (book.filename != null)
                        Text(
                          book.filename!,
                          style: Theme.of(context).textTheme.bodySmall?.copyWith(
                                color: AppTheme.textSecondary,
                              ),
                        ),
                      const SizedBox(height: 8),
                      _StatusChip(status: book.status),
                    ],
                  ),
                ),
              ),
              const SizedBox(height: 16),

              // Actions
              Text(
                'Actions',
                style: Theme.of(context).textTheme.titleMedium?.copyWith(
                      fontWeight: FontWeight.bold,
                    ),
              ),
              const SizedBox(height: 12),
              _ActionButton(
                icon: Icons.picture_as_pdf,
                title: 'View PDF',
                subtitle: 'Read the original document',
                onTap: book.isCompleted
                    ? () {
                        context.push(
                          '/books/${book.id}/pdf?title=${Uri.encodeComponent(book.title)}',
                        );
                      }
                    : null,
              ),
              const SizedBox(height: 8),
              _ActionButton(
                icon: Icons.chat,
                title: 'AI Mentor',
                subtitle: 'Ask questions about this book',
                onTap: book.isCompleted
                    ? () {
                        context.push('/ai/chat/${widget.bookId}');
                      }
                    : null,
              ),
              const SizedBox(height: 8),
              _ActionButton(
                icon: Icons.quiz,
                title: 'Take Quiz',
                subtitle: 'Test your knowledge',
                onTap: book.isCompleted
                    ? () {
                        context.push('/quiz/${widget.bookId}');
                      }
                    : null,
              ),
              const SizedBox(height: 8),
              _ActionButton(
                icon: Icons.summarize,
                title: 'Generate Summary',
                subtitle: 'Get a quick overview',
                onTap: book.isCompleted
                    ? () {
                        context.push('/ai/summarize/${widget.bookId}');
                      }
                    : null,
              ),
              const SizedBox(height: 8),
              _ActionButton(
                icon: Icons.style,
                title: 'Create Flashcards',
                subtitle: 'Generate study flashcards',
                onTap: book.isCompleted
                    ? () {
                        context.push('/ai/flashcards');
                      }
                    : null,
              ),              const SizedBox(height: 8),
              _ActionButton(
                icon: Icons.history,
                title: 'Flashcard History',
                subtitle: 'View all generated flashcards',
                onTap: book.isCompleted
                    ? () {
                        Navigator.push(
                          context,
                          MaterialPageRoute(
                            builder: (_) => FlashcardHistoryScreen(
                              bookId: widget.bookId,
                              bookTitle: book.title,
                            ),
                          ),
                        );
                      }
                    : null,
              ),
              const SizedBox(height: 8),
              _ActionButton(
                icon: Icons.assignment_turned_in,
                title: 'Quiz History',
                subtitle: 'Review past quiz attempts',
                onTap: book.isCompleted
                    ? () {
                        Navigator.push(
                          context,
                          MaterialPageRoute(
                            builder: (_) => QuizHistoryScreen(
                              bookId: widget.bookId,
                              bookTitle: book.title,
                            ),
                          ),
                        );
                      }
                    : null,
              ),              const SizedBox(height: 24),
              const Divider(),
              const SizedBox(height: 8),
              _ActionButton(
                icon: Icons.delete_outline,
                title: 'Delete Book',
                subtitle: 'Remove this book and all its data',
                onTap: () => _showDeleteConfirmation(context, book.title),
              ),
            ],
          ),
        ),
        loading: () => const Center(child: CircularProgressIndicator()),
        error: (error, stack) => Center(
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              const Icon(Icons.error_outline, size: 64, color: AppTheme.errorColor),
              const SizedBox(height: 16),
              Text(
                'Error loading book',
                style: Theme.of(context).textTheme.titleMedium,
              ),
              const SizedBox(height: 8),
              Text(
                error.toString(),
                style: Theme.of(context).textTheme.bodySmall,
                textAlign: TextAlign.center,
              ),
            ],
          ),
        ),
      ),
    );
  }
}

class _StatusChip extends StatelessWidget {
  final String status;

  const _StatusChip({required this.status});

  @override
  Widget build(BuildContext context) {
    Color color;
    IconData icon;
    String text;

    switch (status.toLowerCase()) {
      case 'processing':
        color = AppTheme.warningColor;
        icon = Icons.hourglass_empty;
        text = 'Processing...';
        break;
      case 'completed':
        color = AppTheme.successColor;
        icon = Icons.check_circle;
        text = 'Ready';
        break;
      case 'error':
        color = AppTheme.errorColor;
        icon = Icons.error;
        text = 'Error';
        break;
      default:
        color = AppTheme.textHint;
        icon = Icons.info;
        text = status;
    }

    return Chip(
      avatar: Icon(icon, size: 16, color: color),
      label: Text(text),
      backgroundColor: color.withValues(alpha: 0.1),
      labelStyle: TextStyle(color: color, fontWeight: FontWeight.w600),
    );
  }
}

class _ActionButton extends StatelessWidget {
  final IconData icon;
  final String title;
  final String subtitle;
  final VoidCallback? onTap;

  const _ActionButton({
    required this.icon,
    required this.title,
    required this.subtitle,
    this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    return Card(
      child: InkWell(
        onTap: onTap,
        borderRadius: BorderRadius.circular(12),
        child: Padding(
          padding: const EdgeInsets.all(16),
          child: Row(
            children: [
              Container(
                width: 48,
                height: 48,
                decoration: BoxDecoration(
                  color: onTap != null
                      ? AppTheme.primaryColor.withValues(alpha: 0.1)
                      : AppTheme.textHint.withValues(alpha: 0.1),
                  borderRadius: BorderRadius.circular(8),
                ),
                child: Icon(
                  icon,
                  color: onTap != null ? AppTheme.primaryColor : AppTheme.textHint,
                ),
              ),
              const SizedBox(width: 16),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      title,
                      style: Theme.of(context).textTheme.titleSmall?.copyWith(
                            fontWeight: FontWeight.bold,
                            color: onTap != null ? null : AppTheme.textHint,
                          ),
                    ),
                    Text(
                      subtitle,
                      style: Theme.of(context).textTheme.bodySmall?.copyWith(
                            color: AppTheme.textSecondary,
                          ),
                    ),
                  ],
                ),
              ),
              Icon(
                Icons.chevron_right,
                color: onTap != null ? null : AppTheme.textHint,
              ),
            ],
          ),
        ),
      ),
    );
  }
}

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:file_picker/file_picker.dart';
import '../../../data/models/category_model.dart';
import '../../providers/book_provider.dart';
import '../../providers/category_provider.dart';
import '../../../core/theme/app_theme.dart';

class BooksScreen extends ConsumerStatefulWidget {
  const BooksScreen({super.key});

  @override
  ConsumerState<BooksScreen> createState() => _BooksScreenState();
}

class _BooksScreenState extends ConsumerState<BooksScreen> {
  @override
  void initState() {
    super.initState();
    // Fetch books when screen loads
    Future.microtask(() {
      ref.read(bookProvider.notifier).fetchBooks();
      ref.read(categoryProvider.notifier).fetchCategories();
    });
  }

  Future<void> _handleUploadBook() async {
    // Pick a PDF file
    final result = await FilePicker.platform.pickFiles(
      type: FileType.custom,
      allowedExtensions: ['pdf'],
    );

    if (result == null || result.files.isEmpty) return;

    final file = result.files.first;
    if (file.path == null) return;

    // Show upload dialog
    if (!mounted) return;
    final success = await showDialog<bool>(
      context: context,
      builder: (context) => _UploadDialog(filePath: file.path!, fileName: file.name),
    );

    if (success == true) {
      // Refresh book list
      ref.read(bookProvider.notifier).fetchBooks();
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('Book uploaded successfully!')),
        );
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    final bookState = ref.watch(bookProvider);
    final categories = ref.watch(categoryProvider).categories;

    return Scaffold(
      appBar: AppBar(
        title: const Text('My Books'),
        actions: [
          IconButton(
            icon: const Icon(Icons.refresh),
            onPressed: () => ref.read(bookProvider.notifier).fetchBooks(),
          ),
        ],
      ),
      body: bookState.isLoading && bookState.books.isEmpty
          ? const Center(child: CircularProgressIndicator())
          : bookState.books.isEmpty
              ? _EmptyState(onUpload: _handleUploadBook)
              : RefreshIndicator(
                  onRefresh: () => ref.read(bookProvider.notifier).fetchBooks(),
                  child: ListView.builder(
                    padding: const EdgeInsets.all(16),
                    itemCount: bookState.books.length,
                    itemBuilder: (context, index) {
                      final book = bookState.books[index];
                      CategoryModel? category;
                      try {
                        category = categories.firstWhere(
                          (c) => c.id == book.categoryId,
                        );
                      } catch (e) {
                        category = null;
                      }
                      return _BookCard(
                        book: book,
                        categoryName: category?.name,
                        onTap: () => context.push('/books/${book.id}'),
                      );
                    },
                  ),
                ),
      floatingActionButton: FloatingActionButton.extended(
        onPressed: _handleUploadBook,
        icon: const Icon(Icons.upload_file),
        label: const Text('Upload Book'),
      ),
    );
  }
}

class _EmptyState extends StatelessWidget {
  final VoidCallback onUpload;

  const _EmptyState({required this.onUpload});

  @override
  Widget build(BuildContext context) {
    return Center(
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          const Icon(
            Icons.library_books_outlined,
            size: 100,
            color: AppTheme.textHint,
          ),
          const SizedBox(height: 24),
          Text(
            'No books yet',
            style: Theme.of(context).textTheme.headlineSmall?.copyWith(
                  color: AppTheme.textSecondary,
                ),
          ),
          const SizedBox(height: 8),
          Text(
            'Upload your first PDF book to get started',
            style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                  color: AppTheme.textHint,
                ),
          ),
          const SizedBox(height: 24),
          ElevatedButton.icon(
            onPressed: onUpload,
            icon: const Icon(Icons.upload_file),
            label: const Text('Upload Book'),
          ),
        ],
      ),
    );
  }
}

class _BookCard extends StatelessWidget {
  final dynamic book;
  final String? categoryName;
  final VoidCallback onTap;

  const _BookCard({
    required this.book,
    this.categoryName,
    required this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    return Card(
      margin: const EdgeInsets.only(bottom: 12),
      child: InkWell(
        onTap: onTap,
        borderRadius: BorderRadius.circular(12),
        child: Padding(
          padding: const EdgeInsets.all(16),
          child: Row(
            children: [
              // Book icon
              Container(
                width: 60,
                height: 80,
                decoration: BoxDecoration(
                  color: AppTheme.primaryColor.withValues(alpha: 0.1),
                  borderRadius: BorderRadius.circular(8),
                ),
                child: const Icon(
                  Icons.menu_book,
                  size: 32,
                  color: AppTheme.primaryColor,
                ),
              ),
              const SizedBox(width: 16),
              
              // Book details
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      book.title,
                      style: Theme.of(context).textTheme.titleMedium?.copyWith(
                            fontWeight: FontWeight.bold,
                          ),
                      maxLines: 2,
                      overflow: TextOverflow.ellipsis,
                    ),
                    const SizedBox(height: 4),
                    if (categoryName != null) ...[
                      Chip(
                        label: Text(categoryName!),
                        labelStyle: const TextStyle(fontSize: 12),
                        padding: EdgeInsets.zero,
                        visualDensity: VisualDensity.compact,
                      ),
                      const SizedBox(height: 4),
                    ],
                    Row(
                      children: [
                        _StatusBadge(status: book.status),
                        const SizedBox(width: 8),
                        Text(
                          book.filename ?? '',
                          style: Theme.of(context).textTheme.bodySmall?.copyWith(
                                color: AppTheme.textHint,
                              ),
                          maxLines: 1,
                          overflow: TextOverflow.ellipsis,
                        ),
                      ],
                    ),
                  ],
                ),
              ),
              
              const Icon(Icons.chevron_right),
            ],
          ),
        ),
      ),
    );
  }
}

class _StatusBadge extends StatelessWidget {
  final String status;

  const _StatusBadge({required this.status});

  @override
  Widget build(BuildContext context) {
    Color color;
    String text;

    switch (status.toLowerCase()) {
      case 'processing':
        color = AppTheme.warningColor;
        text = 'Processing';
        break;
      case 'completed':
        color = AppTheme.successColor;
        text = 'Ready';
        break;
      case 'error':
        color = AppTheme.errorColor;
        text = 'Error';
        break;
      default:
        color = AppTheme.textHint;
        text = status;
    }

    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
      decoration: BoxDecoration(
        color: color.withValues(alpha: 0.1),
        borderRadius: BorderRadius.circular(4),
      ),
      child: Text(
        text,
        style: TextStyle(
          color: color,
          fontSize: 11,
          fontWeight: FontWeight.w600,
        ),
      ),
    );
  }
}

class _UploadDialog extends ConsumerStatefulWidget {
  final String filePath;
  final String fileName;

  const _UploadDialog({
    required this.filePath,
    required this.fileName,
  });

  @override
  ConsumerState<_UploadDialog> createState() => _UploadDialogState();
}

class _UploadDialogState extends ConsumerState<_UploadDialog> {
  final _titleController = TextEditingController();
  final _subjectController = TextEditingController();
  String? _selectedCategoryId;
  bool _isUploading = false;
  double _uploadProgress = 0;

  @override
  void initState() {
    super.initState();
    // Set default title from filename
    _titleController.text = widget.fileName.replaceAll('.pdf', '');
  }

  @override
  void dispose() {
    _titleController.dispose();
    _subjectController.dispose();
    super.dispose();
  }

  Future<void> _handleUpload() async {
    setState(() => _isUploading = true);

    final subjectText = _subjectController.text.trim();
    final success = await ref.read(bookProvider.notifier).uploadBook(
      filePath: widget.filePath,
      title: _titleController.text.trim(),
      categoryId: _selectedCategoryId,
      subject: subjectText.isEmpty ? null : subjectText,
      onProgress: (sent, total) {
        setState(() => _uploadProgress = sent / total);
      },
    );

    if (mounted) {
      if (success) {
        Navigator.of(context).pop(true);
      } else {
        setState(() => _isUploading = false);
        final error = ref.read(bookProvider).error;
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text(error ?? 'Upload failed'),
            backgroundColor: AppTheme.errorColor,
          ),
        );
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    final categories = ref.watch(categoryProvider).categories;

    return AlertDialog(
      title: const Text('Upload Book'),
      content: SingleChildScrollView(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            TextField(
              controller: _titleController,
              decoration: const InputDecoration(
                labelText: 'Book Title',
                border: OutlineInputBorder(),
              ),
              enabled: !_isUploading,
            ),
            const SizedBox(height: 16),
            DropdownButtonFormField<String>(
              initialValue: _selectedCategoryId,
              decoration: const InputDecoration(
                labelText: 'Category (Optional)',
                border: OutlineInputBorder(),
              ),
              items: [
                const DropdownMenuItem(
                  value: null,
                  child: Text('No Category'),
                ),
                ...categories.map((category) {
                  return DropdownMenuItem(
                    value: category.id,
                    child: Text(category.name),
                  );
                }),
              ],
              onChanged: _isUploading
                  ? null
                  : (value) {
                      setState(() => _selectedCategoryId = value);
                    },
            ),
            const SizedBox(height: 16),
            TextField(
              controller: _subjectController,
              decoration: const InputDecoration(
                labelText: 'Subject (Optional)',
                hintText: 'e.g., Finance, French, Physics',
                border: OutlineInputBorder(),
                helperText: 'Enter subject for personalized AI tutoring',
                prefixIcon: Icon(Icons.subject),
              ),
              textCapitalization: TextCapitalization.words,
              enabled: !_isUploading,
            ),
            if (_isUploading) ...[
              const SizedBox(height: 16),
              LinearProgressIndicator(value: _uploadProgress),
              const SizedBox(height: 8),
              Text(
                '${(_uploadProgress * 100).toInt()}%',
                textAlign: TextAlign.center,
              ),
            ],
          ],
        ),
      ),
      actions: [
        TextButton(
          onPressed: _isUploading ? null : () => Navigator.of(context).pop(false),
          child: const Text('Cancel'),
        ),
        ElevatedButton(
          onPressed: _isUploading ? null : _handleUpload,
          child: _isUploading
              ? const SizedBox(
                  height: 20,
                  width: 20,
                  child: CircularProgressIndicator(strokeWidth: 2),
                )
              : const Text('Upload'),
        ),
      ],
    );
  }
}

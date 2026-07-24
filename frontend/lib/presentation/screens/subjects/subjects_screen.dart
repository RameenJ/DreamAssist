import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../providers/subject_provider.dart';
import '../../../core/theme/app_theme.dart';

class SubjectsScreen extends ConsumerStatefulWidget {
  const SubjectsScreen({super.key});

  @override
  ConsumerState<SubjectsScreen> createState() => _SubjectsScreenState();
}

class _SubjectsScreenState extends ConsumerState<SubjectsScreen> {
  @override
  void initState() {
    super.initState();
    Future.microtask(() {
      ref.read(subjectProvider.notifier).fetchSubjects();
    });
  }

  void _showAddSubjectDialog() {
    showDialog(
      context: context,
      builder: (context) => _SubjectDialog(
        title: 'Add Subject',
        onSave: (name) async {
          final success = await ref.read(subjectProvider.notifier).createSubject(name);
          if (mounted) {
            if (success) {
              Navigator.of(context).pop();
              ScaffoldMessenger.of(context).showSnackBar(
                const SnackBar(content: Text('Subject created successfully')),
              );
            } else {
              final error = ref.read(subjectProvider).error;
              ScaffoldMessenger.of(context).showSnackBar(
                SnackBar(
                  content: Text(error ?? 'Failed to create subject'),
                  backgroundColor: AppTheme.errorColor,
                ),
              );
            }
          }
        },
      ),
    );
  }

  void _showEditSubjectDialog(String subjectId, String currentName) {
    showDialog(
      context: context,
      builder: (context) => _SubjectDialog(
        title: 'Edit Subject',
        initialName: currentName,
        onSave: (name) async {
          final success = await ref.read(subjectProvider.notifier).updateSubject(subjectId, name);
          if (mounted) {
            if (success) {
              Navigator.of(context).pop();
              ScaffoldMessenger.of(context).showSnackBar(
                const SnackBar(content: Text('Subject updated successfully')),
              );
            } else {
              final error = ref.read(subjectProvider).error;
              ScaffoldMessenger.of(context).showSnackBar(
                SnackBar(
                  content: Text(error ?? 'Failed to update subject'),
                  backgroundColor: AppTheme.errorColor,
                ),
              );
            }
          }
        },
      ),
    );
  }

  void _showDeleteConfirmation(String subjectId, String name) {
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Delete Subject'),
        content: Text('Are you sure you want to delete "$name"? Books in this subject will become uncategorized.'),
        actions: [
          TextButton(
            onPressed: () => Navigator.of(context).pop(),
            child: const Text('Cancel'),
          ),
          ElevatedButton(
            onPressed: () async {
              final success = await ref.read(subjectProvider.notifier).deleteSubject(subjectId);
              if (mounted) {
                Navigator.of(context).pop();
                if (success) {
                  ScaffoldMessenger.of(context).showSnackBar(
                    const SnackBar(content: Text('Subject deleted successfully')),
                  );
                } else {
                  final error = ref.read(subjectProvider).error;
                  ScaffoldMessenger.of(context).showSnackBar(
                    SnackBar(
                      content: Text(error ?? 'Failed to delete subject'),
                      backgroundColor: AppTheme.errorColor,
                    ),
                  );
                }
              }
            },
            style: ElevatedButton.styleFrom(
              backgroundColor: AppTheme.errorColor,
            ),
            child: const Text('Delete'),
          ),
        ],
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    final subjectState = ref.watch(subjectProvider);

    return Scaffold(
      appBar: AppBar(
        title: const Text('Subjects'),
      ),
      body: subjectState.isLoading && subjectState.subjects.isEmpty
          ? const Center(child: CircularProgressIndicator())
          : subjectState.subjects.isEmpty
              ? _EmptyState(onAdd: _showAddSubjectDialog)
              : ListView.builder(
                  padding: const EdgeInsets.all(16),
                  itemCount: subjectState.subjects.length,
                  itemBuilder: (context, index) {
                    final subject = subjectState.subjects[index];
                    return Card(
                      margin: const EdgeInsets.only(bottom: 8),
                      child: ListTile(
                        leading: CircleAvatar(
                          backgroundColor: AppTheme.primaryColor.withValues(alpha: 0.1),
                          child: const Icon(Icons.book, color: AppTheme.primaryColor),
                        ),
                        title: Text(
                          subject.name,
                          style: const TextStyle(fontWeight: FontWeight.w600),
                        ),
                        trailing: PopupMenuButton(
                          itemBuilder: (context) => [
                            const PopupMenuItem(
                              value: 'edit',
                              child: Row(
                                children: [
                                  Icon(Icons.edit, size: 20),
                                  SizedBox(width: 8),
                                  Text('Edit'),
                                ],
                              ),
                            ),
                            const PopupMenuItem(
                              value: 'delete',
                              child: Row(
                                children: [
                                  Icon(Icons.delete, size: 20, color: AppTheme.errorColor),
                                  SizedBox(width: 8),
                                  Text('Delete', style: TextStyle(color: AppTheme.errorColor)),
                                ],
                              ),
                            ),
                          ],
                          onSelected: (value) {
                            if (value == 'edit') {
                              _showEditSubjectDialog(subject.id, subject.name);
                            } else if (value == 'delete') {
                              _showDeleteConfirmation(subject.id, subject.name);
                            }
                          },
                        ),
                      ),
                    );
                  },
                ),
      floatingActionButton: FloatingActionButton.extended(
        onPressed: _showAddSubjectDialog,
        icon: const Icon(Icons.add),
        label: const Text('Add Subject'),
      ),
    );
  }
}

class _EmptyState extends StatelessWidget {
  final VoidCallback onAdd;

  const _EmptyState({required this.onAdd});

  @override
  Widget build(BuildContext context) {
    return Center(
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          const Icon(
            Icons.book_outlined,
            size: 100,
            color: AppTheme.textHint,
          ),
          const SizedBox(height: 24),
          Text(
            'No subjects yet',
            style: Theme.of(context).textTheme.headlineSmall?.copyWith(
                  color: AppTheme.textSecondary,
                ),
          ),
          const SizedBox(height: 8),
          Text(
            'Create subjects to organize your books',
            style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                  color: AppTheme.textHint,
                ),
          ),
          const SizedBox(height: 24),
          ElevatedButton.icon(
            onPressed: onAdd,
            icon: const Icon(Icons.add),
            label: const Text('Add Subject'),
          ),
        ],
      ),
    );
  }
}

class _SubjectDialog extends StatefulWidget {
  final String title;
  final String? initialName;
  final Future<void> Function(String name) onSave;

  const _SubjectDialog({
    required this.title,
    this.initialName,
    required this.onSave,
  });

  @override
  State<_SubjectDialog> createState() => _SubjectDialogState();
}

class _SubjectDialogState extends State<_SubjectDialog> {
  late final TextEditingController _controller;
  bool _isSaving = false;

  @override
  void initState() {
    super.initState();
    _controller = TextEditingController(text: widget.initialName);
  }

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  Future<void> _save() async {
    final name = _controller.text.trim();
    if (name.isEmpty) return;

    setState(() => _isSaving = true);
    await widget.onSave(name);
    if (mounted) {
      setState(() => _isSaving = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return AlertDialog(
      title: Text(widget.title),
      content: TextField(
        controller: _controller,
        decoration: const InputDecoration(
          labelText: 'Subject Name',
          border: OutlineInputBorder(),
        ),
        enabled: !_isSaving,
        autofocus: true,
        onSubmitted: (_) => _save(),
      ),
      actions: [
        TextButton(
          onPressed: _isSaving ? null : () => Navigator.of(context).pop(),
          child: const Text('Cancel'),
        ),
        ElevatedButton(
          onPressed: _isSaving ? null : _save,
          child: _isSaving
              ? const SizedBox(
                  height: 20,
                  width: 20,
                  child: CircularProgressIndicator(strokeWidth: 2),
                )
              : const Text('Save'),
        ),
      ],
    );
  }
}

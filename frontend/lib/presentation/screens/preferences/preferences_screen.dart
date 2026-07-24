import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import '../../../core/theme/app_theme.dart';
import '../../providers/subject_profile_provider.dart';
import '../../providers/auth_provider.dart';
import '../../../data/models/subject_profile_model.dart';
import 'preference_dialogs.dart' as dialogs;

class PreferencesScreen extends ConsumerStatefulWidget {
  final bool isInitialSetup;

  const PreferencesScreen({super.key, this.isInitialSetup = false});

  @override
  ConsumerState<PreferencesScreen> createState() => _PreferencesScreenState();
}

class _PreferencesScreenState extends ConsumerState<PreferencesScreen> {
  @override
  void initState() {
    super.initState();
    // Load existing profiles
    Future.microtask(() => ref.read(subjectProfileProvider.notifier).loadProfiles());
  }

  void _showAddSubjectDialog() {
    showDialog(
      context: context,
      builder: (context) => const dialogs.AddSubjectDialog(),
    );
  }

  void _showEditSubjectDialog(SubjectProfileModel profile) {
    showDialog(
      context: context,
      builder: (context) => dialogs.EditSubjectDialog(profile: profile),
    );
  }

  @override
  Widget build(BuildContext context) {
    final profileState = ref.watch(subjectProfileProvider);
    final user = ref.watch(authProvider).user;

    return Scaffold(
      appBar: AppBar(
        title: const Text('Study Preferences'),
        leading: widget.isInitialSetup
            ? null
            : IconButton(
                icon: const Icon(Icons.arrow_back),
                onPressed: () => context.pop(),
              ),
        actions: [
          if (!widget.isInitialSetup)
            IconButton(
              icon: const Icon(Icons.person),
              onPressed: () => context.push('/profile'),
            ),
        ],
      ),
      body: Column(
        children: [
          // Welcome header
          Container(
            width: double.infinity,
            padding: const EdgeInsets.all(20),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  widget.isInitialSetup
                      ? 'Welcome, ${user?.firstname ?? ""}!'
                      : 'My Subjects',
                  style: Theme.of(context).textTheme.headlineSmall?.copyWith(
                        fontWeight: FontWeight.bold,
                        color: AppTheme.primaryColor,
                      ),
                ),
                const SizedBox(height: 4),
                Text(
                  widget.isInitialSetup
                      ? 'Add subjects you want to study and take a quick quiz to personalize your learning experience.'
                      : 'Manage your subjects and preferences',
                  style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                        color: AppTheme.textSecondary,
                      ),
                ),
              ],
            ),
          ),
          // Subject list
          Expanded(
            child: profileState.isLoading
                ? const Center(child: CircularProgressIndicator())
                : profileState.profiles.isEmpty
                    ? _buildEmptyState()
                    : ListView.builder(
                        padding: const EdgeInsets.all(16),
                        itemCount: profileState.profiles.length,
                        itemBuilder: (context, index) {
                          final profile = profileState.profiles[index];
                          return _SubjectCard(
                            profile: profile,
                            onTap: () => _showEditSubjectDialog(profile),
                            onDelete: () async {
                              final confirm = await _showDeleteConfirmation(profile.subject);
                              if (confirm == true) {
                                ref.read(subjectProfileProvider.notifier).deleteProfile(profile.subject);
                              }
                            },
                            onRetakeQuiz: () {
                              context.push('/diagnostic-quiz/${profile.subject}');
                            },
                          );
                        },
                      ),
          ),
          // Bottom action buttons
          Padding(
            padding: const EdgeInsets.all(16),
            child: Column(
              children: [
                SizedBox(
                  width: double.infinity,
                  child: ElevatedButton.icon(
                    onPressed: _showAddSubjectDialog,
                    icon: const Icon(Icons.add),
                    label: const Text('Add New Subject'),
                  ),
                ),
                if (widget.isInitialSetup) ...[
                  const SizedBox(height: 12),
                  SizedBox(
                    width: double.infinity,
                    child: TextButton(
                      onPressed: () => context.go('/home'),
                      child: const Text('Skip for Now'),
                    ),
                  ),
                  const SizedBox(height: 8),
                  if (profileState.profiles.isNotEmpty)
                    SizedBox(
                      width: double.infinity,
                      child: ElevatedButton(
                        onPressed: () => context.go('/home'),
                        child: const Text('Continue to Home'),
                      ),
                    ),
                ],
                // Always show Go to Home button for all users
                const SizedBox(height: 12),
                SizedBox(
                  width: double.infinity,
                  child: ElevatedButton(
                    onPressed: () => context.go('/home'),
                    child: const Text('Go to Home'),
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildEmptyState() {
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(32),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(
              Icons.school_outlined,
              size: 80,
              color: AppTheme.textSecondary.withValues(alpha: 0.5),
            ),
            const SizedBox(height: 16),
            Text(
              'No subjects yet',
              style: Theme.of(context).textTheme.titleLarge?.copyWith(
                    color: AppTheme.textSecondary,
                  ),
            ),
            const SizedBox(height: 8),
            Text(
              'Add subjects you want to study and take diagnostic quizzes to get personalized recommendations',
              textAlign: TextAlign.center,
              style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                    color: AppTheme.textSecondary.withValues(alpha: 0.7),
                  ),
            ),
          ],
        ),
      ),
    );
  }

  Future<bool?> _showDeleteConfirmation(String subject) {
    return showDialog<bool>(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Delete Subject'),
        content: Text('Are you sure you want to remove "$subject"?'),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context, false),
            child: const Text('Cancel'),
          ),
          TextButton(
            onPressed: () => Navigator.pop(context, true),
            style: TextButton.styleFrom(foregroundColor: AppTheme.errorColor),
            child: const Text('Delete'),
          ),
        ],
      ),
    );
  }
}

class _SubjectCard extends StatelessWidget {
  final SubjectProfileModel profile;
  final VoidCallback onTap;
  final VoidCallback onDelete;
  final VoidCallback onRetakeQuiz;

  const _SubjectCard({
    required this.profile,
    required this.onTap,
    required this.onDelete,
    required this.onRetakeQuiz,
  });

  IconData _getLevelIcon() {
    switch (profile.level) {
      case 'beginner':
        return Icons.star_border;
      case 'intermediate':
        return Icons.star_half;
      case 'advanced':
        return Icons.star;
      default:
        return Icons.star_outline;
    }
  }

  Color _getLevelColor() {
    switch (profile.level) {
      case 'beginner':
        return Colors.green;
      case 'intermediate':
        return Colors.orange;
      case 'advanced':
        return Colors.red;
      default:
        return AppTheme.textSecondary;
    }
  }

  @override
  Widget build(BuildContext context) {
    return Card(
      margin: const EdgeInsets.only(bottom: 12),
      child: InkWell(
        onTap: onTap,
        borderRadius: BorderRadius.circular(12),
        child: Padding(
          padding: const EdgeInsets.all(16),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Row(
                children: [
                  Expanded(
                    child: Text(
                      profile.subject,
                      style:
                          Theme.of(context).textTheme.titleMedium?.copyWith(
                                fontWeight: FontWeight.bold,
                              ),
                    ),
                  ),
                  PopupMenuButton(
                    itemBuilder: (context) => [
                      const PopupMenuItem(
                        value: 'retake',
                        child: Row(
                          children: [
                            Icon(Icons.quiz),
                            SizedBox(width: 8),
                            Text('Retake Quiz'),
                          ],
                        ),
                      ),
                      const PopupMenuItem(
                        value: 'delete',
                        child: Row(
                          children: [
                            Icon(Icons.delete, color: AppTheme.errorColor),
                            SizedBox(width: 8),
                            Text('Delete', style: TextStyle(color: AppTheme.errorColor)),
                          ],
                        ),
                      ),
                    ],
                    onSelected: (value) {
                      if (value == 'delete') {
                        onDelete();
                      } else if (value == 'retake') {
                        onRetakeQuiz();
                      }
                    },
                  ),
                ],
              ),
              const SizedBox(height: 12),
              Wrap(
                spacing: 8,
                runSpacing: 8,
                children: [
                  _Chip(
                    icon: _getLevelIcon(),
                    label: profile.level.toUpperCase(),
                    color: _getLevelColor(),
                  ),
                  _Chip(
                    icon: Icons.speed,
                    label: profile.studyPace,
                    color: AppTheme.primaryColor,
                  ),
                  _Chip(
                    icon: Icons.style,
                    label: profile.studyStyle,
                    color: AppTheme.accentColor,
                  ),
                ],
              ),
              const SizedBox(height: 8),
              Row(
                children: [
                  const Icon(
                    Icons.timer_outlined,
                    size: 16,
                    color: AppTheme.textSecondary,
                  ),
                  const SizedBox(width: 4),
                  Expanded(
                    child: Text(
                      profile.breakPreference,
                      style: Theme.of(context).textTheme.bodySmall?.copyWith(
                            color: AppTheme.textSecondary,
                          ),
                    ),
                  ),
                  Text(
                    profile.assessmentMethod == 'quiz' ? '✓ Assessed' : 'Manual',
                    style: Theme.of(context).textTheme.bodySmall?.copyWith(
                          color: AppTheme.textSecondary,
                          fontStyle: FontStyle.italic,
                        ),
                  ),
                ],
              ),
            ],
          ),
        ),
      ),
    );
  }
}

class _Chip extends StatelessWidget {
  final IconData icon;
  final String label;
  final Color color;

  const _Chip({
    required this.icon,
    required this.label,
    required this.color,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 6),
      decoration: BoxDecoration(
        color: color.withValues(alpha: 0.1),
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: color.withValues(alpha: 0.3)),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(icon, size: 14, color: color),
          const SizedBox(width: 4),
          Text(
            label,
            style: TextStyle(
              fontSize: 12,
              color: color,
              fontWeight: FontWeight.w600,
            ),
          ),
        ],
      ),
    );
  }
}

// Continued in next part...

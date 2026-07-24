import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import '../../providers/auth_provider.dart';
import '../../providers/mood_provider.dart';
import '../../providers/study_planner_provider.dart';
import '../../widgets/mood_logger_modal.dart';
import '../../../core/theme/app_theme.dart';

class HomeScreen extends ConsumerStatefulWidget {
  const HomeScreen({super.key});

  @override
  ConsumerState<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends ConsumerState<HomeScreen> {
  @override
  void initState() {
    super.initState();
    print('🏠 [HomeScreen] initState called');
    // Check mood status and preload current plan after build
    WidgetsBinding.instance.addPostFrameCallback((_) {
      print('🏠 [HomeScreen] PostFrameCallback executing');
      _initializeHomeScreen();
    });
  }

  Future<void> _initializeHomeScreen() async {
    print('🏠 [HomeScreen] _initializeHomeScreen started');
    
    // Check if widget is still mounted before async operations
    if (!mounted) {
      print('🏠 [HomeScreen] Widget not mounted before initialization');
      return;
    }
    
    // 🆕 Preload the current active plan into memory (in-memory only, no persistence)
    print('🆕 [HomeScreen] Preloading current active plan...');
    try {
      await ref.read(currentPlanProvider.future);
      print('🆕 [HomeScreen] ✅ Current active plan preloaded successfully');
    } catch (e) {
      print('🆕 [HomeScreen] ⚠️ No active plans available or error fetching: $e');
      // This is not an error - the user might not have any plans yet
    }
    
    // Check if user has logged mood today
    await ref.read(moodProvider.notifier).checkTodayMood();
    
    // Check mounted state after async operations
    if (!mounted) {
      print('🏠 [HomeScreen] Widget not mounted after check');
      return;
    }
    
    // Show modal if needed
    final moodState = ref.read(moodProvider);
    print('🏠 [HomeScreen] Mood state: showModal=${moodState.showModal}, isLoading=${moodState.isLoading}, error=${moodState.error}');
    
    if (moodState.showModal && mounted) {
      print('🏠 [HomeScreen] Showing mood logger modal');
      showDialog(
        context: context,
        barrierDismissible: false,
        builder: (context) => const MoodLoggerModal(),
      );
    } else {
      print('🏠 [HomeScreen] Not showing modal - showModal=${moodState.showModal}, mounted=$mounted');
    }
  }

  @override
  Widget build(BuildContext context) {
    final authState = ref.watch(authProvider);
    final user = authState.user;

    return Scaffold(
      appBar: AppBar(
        title: const Text('DreamAssist'),
        actions: [
          IconButton(
            icon: const Icon(Icons.person),
            onPressed: () => context.push('/profile'),
          ),
        ],
      ),
      body: user == null
          ? const Center(child: CircularProgressIndicator())
          : SingleChildScrollView(
              padding: const EdgeInsets.all(16),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  // Welcome section
                  _WelcomeCard(userName: user.firstname),
                  const SizedBox(height: 24),

                  // Quick actions
                  Text(
                    'Quick Actions',
                    style: Theme.of(context).textTheme.titleLarge?.copyWith(
                          fontWeight: FontWeight.bold,
                        ),
                  ),
                  const SizedBox(height: 16),
                  _QuickActionsGrid(),
                  const SizedBox(height: 24),

                  // Features section
                  Text(
                    'Features',
                    style: Theme.of(context).textTheme.titleLarge?.copyWith(
                          fontWeight: FontWeight.bold,
                        ),
                  ),
                  const SizedBox(height: 16),
                  _FeaturesGrid(),
                ],
              ),
            ),
    );
  }
}

class _WelcomeCard extends StatelessWidget {
  final String userName;

  const _WelcomeCard({required this.userName});

  @override
  Widget build(BuildContext context) {
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(24),
      decoration: BoxDecoration(
        gradient: const LinearGradient(
          colors: [AppTheme.primaryColor, AppTheme.secondaryColor],
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
        ),
        borderRadius: BorderRadius.circular(16),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            'Welcome back,',
            style: Theme.of(context).textTheme.titleMedium?.copyWith(
                  color: Colors.white.withValues(alpha: 0.9),
                ),
          ),
          const SizedBox(height: 4),
          Text(
            userName,
            style: Theme.of(context).textTheme.headlineMedium?.copyWith(
                  color: Colors.white,
                  fontWeight: FontWeight.bold,
                ),
          ),
          const SizedBox(height: 8),
          Text(
            'Ready to continue your learning journey?',
            style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                  color: Colors.white.withValues(alpha: 0.9),
                ),
          ),
        ],
      ),
    );
  }
}

class _QuickActionsGrid extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    return Row(
      children: [
        Expanded(
          child: _ActionCard(
            icon: Icons.upload_file,
            title: 'Upload Book',
            color: AppTheme.primaryColor,
            onTap: () => context.push('/books'),
          ),
        ),
        const SizedBox(width: 12),
        Expanded(
          child: _ActionCard(
            icon: Icons.book,
            title: 'Subjects',
            color: AppTheme.secondaryColor,
            onTap: () => context.push('/subjects'),
          ),
        ),
      ],
    );
  }
}

class _FeaturesGrid extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    final features = [
      const _FeatureItem(
        icon: Icons.library_books,
        title: 'My Books',
        description: 'Access and manage your uploaded books',
        color: Colors.blue,
        route: '/books',
      ),
      const _FeatureItem(
        icon: Icons.calendar_month,
        title: 'Study Planner',
        description: 'Create and manage your study plans',
        color: Colors.indigo,
        route: '/study-planner',
      ),
      const _FeatureItem(
        icon: Icons.today,
        title: 'Today\'s Schedule',
        description: 'View all tasks across active plans',
        color: Colors.green,
        route: '/daily-schedule',
      ),
      const _FeatureItem(
        icon: Icons.calendar_month,
        title: 'Weekly Schedule',
        description: 'View your schedule for the week',
        color: Colors.cyan,
        route: '/weekly-schedule',
      ),
      const _FeatureItem(
        icon: Icons.smart_toy,
        title: 'AI Mentor',
        description: 'Get AI-powered assistance with your studies',
        color: Colors.purple,
        route: '/books',
      ),
      const _FeatureItem(
        icon: Icons.quiz,
        title: 'Quizzes',
        description: 'Test your knowledge with AI-generated quizzes',
        color: Colors.orange,
        route: '/books',
      ),
      const _FeatureItem(
        icon: Icons.summarize,
        title: 'Summaries',
        description: 'Generate quick summaries of your content',
        color: Colors.green,
        route: '/ai/summarize',
      ),
      const _FeatureItem(
        icon: Icons.style,
        title: 'Flashcards',
        description: 'Create flashcards for effective memorization',
        color: Colors.red,
        route: '/ai/flashcards',
      ),
      const _FeatureItem(
        icon: Icons.insights,
        title: 'Progress',
        description: 'Track your learning progress and statistics',
        color: Colors.teal,
        route: '/progress',
      ),
      const _FeatureItem(
        icon: Icons.psychology,
        title: 'Persona Chat',
        description: 'Chat with AI mentors like Einstein & Curie',
        color: Color(0xFF9C27B0),
        route: '/persona-chat',
      ),
      const _FeatureItem(
        icon: Icons.mood,
        title: 'Mood Log',
        description: 'Track your mood trends and emotional wellness',
        color: Colors.pink,
        route: '/mood-log',
      ),
    ];

    return GridView.builder(
      shrinkWrap: true,
      physics: const NeverScrollableScrollPhysics(),
      gridDelegate: const SliverGridDelegateWithFixedCrossAxisCount(
        crossAxisCount: 2,
        crossAxisSpacing: 12,
        mainAxisSpacing: 12,
        childAspectRatio: 1.1,
      ),
      itemCount: features.length,
      itemBuilder: (context, index) {
        final feature = features[index];
        return _FeatureCard(feature: feature);
      },
    );
  }
}

class _ActionCard extends StatelessWidget {
  final IconData icon;
  final String title;
  final Color color;
  final VoidCallback onTap;

  const _ActionCard({
    required this.icon,
    required this.title,
    required this.color,
    required this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    return Card(
      child: InkWell(
        onTap: onTap,
        borderRadius: BorderRadius.circular(12),
        child: Padding(
          padding: const EdgeInsets.all(16),
          child: Column(
            children: [
              Icon(icon, size: 32, color: color),
              const SizedBox(height: 8),
              Text(
                title,
                style: Theme.of(context).textTheme.titleSmall,
                textAlign: TextAlign.center,
              ),
            ],
          ),
        ),
      ),
    );
  }
}

class _FeatureItem {
  final IconData icon;
  final String title;
  final String description;
  final Color color;
  final String route;

  const _FeatureItem({
    required this.icon,
    required this.title,
    required this.description,
    required this.color,
    required this.route,
  });
}

class _FeatureCard extends StatelessWidget {
  final _FeatureItem feature;

  const _FeatureCard({required this.feature});

  @override
  Widget build(BuildContext context) {
    return Card(
      child: InkWell(
        onTap: () => context.push(feature.route),
        borderRadius: BorderRadius.circular(12),
        child: Padding(
          padding: const EdgeInsets.all(16),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Icon(feature.icon, size: 32, color: feature.color),
              const Spacer(),
              Text(
                feature.title,
                style: Theme.of(context).textTheme.titleMedium?.copyWith(
                      fontWeight: FontWeight.bold,
                    ),
              ),
              const SizedBox(height: 4),
              Text(
                feature.description,
                style: Theme.of(context).textTheme.bodySmall?.copyWith(
                      color: AppTheme.textSecondary,
                    ),
                maxLines: 2,
                overflow: TextOverflow.ellipsis,
              ),
            ],
          ),
        ),
      ),
    );
  }
}

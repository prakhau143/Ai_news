from django.db import models
from django.utils import timezone


class NewsItem(models.Model):
    TAG_CHOICES = [('NEW', 'New'), ('HOT', 'Hot'), ('TRENDING', 'Trending')]
    CATEGORY_CHOICES = [
        ('OpenAI', 'OpenAI'), ('Google', 'Google'), ('Anthropic', 'Anthropic'),
        ('Meta', 'Meta'), ('DeepSeek', 'DeepSeek'), ('AI Agents', 'AI Agents'),
        ('Research', 'Research'), ('Startup', 'Startup'), ('Healthcare', 'Healthcare'),
        ('Robotics', 'Robotics'), ('Tools', 'Tools'), ('General AI', 'General AI'),
    ]

    title = models.CharField(max_length=500)
    summary = models.TextField(blank=True)
    full_content = models.TextField(blank=True)
    source = models.CharField(max_length=200, blank=True)
    source_url = models.URLField(max_length=1000, blank=True)
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES, default='General AI')
    tag = models.CharField(max_length=20, choices=TAG_CHOICES, default='NEW')
    importance = models.IntegerField(default=5)
    image_seed = models.IntegerField(default=0)   # deterministic picsum seed
    published_at = models.DateTimeField(default=timezone.now)
    created_at = models.DateTimeField(auto_now_add=True)
    verified = models.BooleanField(default=False)

    class Meta:
        ordering = ['-published_at']

    def __str__(self):
        return self.title[:80]

    @property
    def theme(self):
        """Return gradient/icon/logo for this category."""
        return CATEGORY_THEMES.get(self.category, CATEGORY_THEMES['General AI'])

    @property
    def card_image_url(self):
        """Deterministic picsum image — same news always gets same image."""
        seed = (self.image_seed or self.pk or 1) % 1000
        return f"https://picsum.photos/seed/{self.category.replace(' ', '')}{seed}/600/400"


# Category visual themes used in templates and JS
CATEGORY_THEMES = {
    'OpenAI': {
        'gradient': 'linear-gradient(135deg,#10a37f 0%,#0d5e4a 100%)',
        'icon': '🤖', 'logo': 'OpenAI',
        'seeds': [42, 156, 287, 394, 521, 633, 744, 855, 921, 199],
    },
    'Google': {
        'gradient': 'linear-gradient(135deg,#4285f4 0%,#1a2e6b 100%)',
        'icon': '🔍', 'logo': 'Google',
        'seeds': [78, 203, 445, 667, 890, 112, 334, 556, 778, 999],
    },
    'Anthropic': {
        'gradient': 'linear-gradient(135deg,#7c3aed 0%,#4c1d95 100%)',
        'icon': '✨', 'logo': 'Anthropic',
        'seeds': [15, 127, 239, 351, 463, 575, 687, 799, 811, 923],
    },
    'Meta': {
        'gradient': 'linear-gradient(135deg,#0064e1 0%,#002b5c 100%)',
        'icon': '🌐', 'logo': 'Meta',
        'seeds': [88, 176, 264, 352, 440, 528, 616, 704, 792, 880],
    },
    'DeepSeek': {
        'gradient': 'linear-gradient(135deg,#00a3ff 0%,#003d66 100%)',
        'icon': '🔮', 'logo': 'DeepSeek',
        'seeds': [33, 99, 165, 231, 297, 363, 429, 495, 561, 627],
    },
    'AI Agents': {
        'gradient': 'linear-gradient(135deg,#f97316 0%,#9a3412 100%)',
        'icon': '⚡', 'logo': 'Agents',
        'seeds': [55, 110, 165, 220, 275, 330, 385, 440, 495, 550],
    },
    'Research': {
        'gradient': 'linear-gradient(135deg,#14b8a6 0%,#0f3b3a 100%)',
        'icon': '🔬', 'logo': 'Research',
        'seeds': [22, 44, 66, 88, 110, 132, 154, 176, 198, 220],
    },
    'Startup': {
        'gradient': 'linear-gradient(135deg,#eab308 0%,#854d0e 100%)',
        'icon': '🚀', 'logo': 'Startup',
        'seeds': [71, 142, 213, 284, 355, 426, 497, 568, 639, 710],
    },
    'Healthcare': {
        'gradient': 'linear-gradient(135deg,#ec4899 0%,#831843 100%)',
        'icon': '🏥', 'logo': 'HealthAI',
        'seeds': [19, 38, 57, 76, 95, 114, 133, 152, 171, 190],
    },
    'Robotics': {
        'gradient': 'linear-gradient(135deg,#a855f7 0%,#4c1d95 100%)',
        'icon': '🦾', 'logo': 'Robotics',
        'seeds': [61, 122, 183, 244, 305, 366, 427, 488, 549, 610],
    },
    'Tools': {
        'gradient': 'linear-gradient(135deg,#3b82f6 0%,#1e3a8a 100%)',
        'icon': '🛠️', 'logo': 'AI Tools',
        'seeds': [47, 94, 141, 188, 235, 282, 329, 376, 423, 470],
    },
    'General AI': {
        'gradient': 'linear-gradient(135deg,#6366f1 0%,#312e81 100%)',
        'icon': '🧠', 'logo': 'AI News',
        'seeds': [13, 26, 39, 52, 65, 78, 91, 104, 117, 130],
    },
}

from django.db import models


class Department(models.Model):
    department_name = models.CharField(max_length=256)

    def __str__(self):
        return self.department_name


class GroupList(models.Model):
    group_list_name = models.CharField(max_length=256)
    department_id = models.ForeignKey(Department, on_delete=models.CASCADE)

    def __str__(self):
        return self.group_list_name


class Group(models.Model):
    group_name = models.CharField(max_length=256)
    group_list_id = models.ForeignKey(GroupList, on_delete=models.CASCADE)

    def __str__(self):
        return self.group_name


class DayOfWeek(models.Model):
    day_of_week = models.CharField(max_length=256)

    def __str__(self):
        return self.day_of_week


class TimeTableDay(models.Model):
    group_id = models.ForeignKey(Group, on_delete=models.CASCADE)
    day_of_week = models.ForeignKey(DayOfWeek, on_delete=models.CASCADE)
    pair_number = models.IntegerField(blank=True)
    pair_other_name = models.CharField(max_length=256, blank=True)
    is_numerator = models.BooleanField()
    subject = models.CharField(max_length=256, blank=True)
    teacher = models.CharField(max_length=256, blank=True)
    audience = models.CharField(max_length=256, blank=True)

    def __str__(self):
        return f"{self.pair_other_name if self.pair_other_name else self.pair_number} [{self.audience}] " \
               f"{self.subject} ({self.teacher})"


class Role(models.Model):
    role = models.CharField(max_length=256)

    def __str__(self):
        return self.role

class User(models.Model):
    vk_id = models.CharField(max_length=256,null=True, blank=True)
    tg_id = models.CharField(max_length=256,null=True, blank=True)
    group_id = models.ForeignKey(Group, on_delete=models.SET_NULL, null=True, blank=True)
    role_id = models.ForeignKey(Role, on_delete=models.SET_NULL, null=True, blank=True)
    show_start_pair = models.BooleanField(default=True, blank=True)
    teacher_name = models.CharField(max_length=256, blank=True)

    def __str__(self):
        return self.vk_id if self.vk_id else self.tg_id

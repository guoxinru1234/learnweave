# ORM框架SQLAlchemy入门

> 模块：SQL与数据库 | 编号：第40讲 | Python数据分析实战

---

## 1. 概念

**ORM（Object-Relational Mapping，对象关系映射）** 是一种编程技术，它将数据库中的表（关系型结构）映射为Python中的类（对象结构），将表中的行映射为类的实例，将表中的列映射为实例的属性。这样，开发者就可以用面向对象的方式操作数据库，而不必直接编写SQL语句。

**SQLAlchemy** 是Python中最流行的ORM框架之一，它提供了完整的企业级持久化模型。其核心思想是：**用Python对象来表达业务逻辑，由框架自动翻译成对应的SQL语句并执行**。

**生活化类比**：可以把ORM想象成一位"翻译官"。你（Python程序员）用中文（对象操作）向翻译官表达需求，翻译官将其翻译成英文（SQL语句）与外国友人（数据库）交流。你不需要精通英文（SQL），只需要专注于自己的表达即可。

**适用场景**：当你的数据分析项目需要频繁读写数据库，且希望代码可维护性高、跨数据库兼容性强时，ORM是理想选择。尤其适合团队协作开发、项目迭代频繁的场景。

---

## 2. 核心API与原理

| API/方法 | 签名 | 参数说明 | 返回值 | 说明 |
|---------|------|---------|--------|------|
| `create_engine()` | `create_engine(url, echo=False)` | `url`: 数据库连接字符串；`echo`: 是否打印SQL日志 | `Engine` 对象 | 创建数据库引擎，是连接数据库的入口 |
| `declarative_base()` | `declarative_base()` | 无 | `Base` 类 | 创建ORM基类，所有模型类需继承它 |
| `sessionmaker()` | `sessionmaker(bind=engine)` | `bind`: 绑定的引擎 | `Session` 工厂类 | 创建会话工厂，用于生成会话对象 |
| `session.add()` | `add(instance)` | `instance`: 模型实例 | `None` | 将对象添加到会话（待提交状态） |
| `session.commit()` | `commit()` | 无 | `None` | 提交事务，将会话中的变更持久化到数据库 |
| `session.query()` | `query(Model)` | `Model`: 模型类 | `Query` 对象 | 创建查询对象，支持链式调用过滤、排序等 |

**核心原理**：SQLAlchemy通过 `Engine` 管理数据库连接池，通过 `Session` 管理事务和对象状态。当你操作一个ORM对象时，SQLAlchemy会跟踪其状态变化（新增、修改、删除），并在 `commit()` 时将这些变化批量转换为SQL语句执行。

---

## 3. 代码示例

### 示例1：基础建表与插入数据（入门）

```python
# 导入必要的模块
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# 1. 创建引擎（使用SQLite内存数据库，无需安装额外驱动）
engine = create_engine('sqlite:///demo.db', echo=True)  # echo=True会打印SQL日志

# 2. 创建基类
Base = declarative_base()

# 3. 定义模型类（对应数据库中的表）
class User(Base):
    __tablename__ = 'users'  # 指定表名
    
    id = Column(Integer, primary_key=True)  # 主键
    name = Column(String(50))               # 姓名，最大长度50
    age = Column(Integer)                   # 年龄

# 4. 创建所有表
Base.metadata.create_all(engine)

# 5. 创建会话
Session = sessionmaker(bind=engine)
session = Session()

# 6. 创建对象并添加
user1 = User(name='张三', age=25)
user2 = User(name='李四', age=30)
session.add(user1)
session.add(user2)

# 7. 提交事务
session.commit()

# 8. 查询验证
users = session.query(User).all()
for u in users:
    print(f"ID: {u.id}, 姓名: {u.name}, 年龄: {u.age}")
# 输出:
# ID: 1, 姓名: 张三, 年龄: 25
# ID: 2, 姓名: 李四, 年龄: 30

session.close()
```

### 示例2：查询与过滤（进阶）

```python
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

engine = create_engine('sqlite:///demo.db')
Base = declarative_base()

class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    name = Column(String(50))
    age = Column(Integer)

Session = sessionmaker(bind=engine)
session = Session()

# 基础查询：获取所有用户
all_users = session.query(User).all()
print(f"总用户数: {len(all_users)}")

# 条件查询：年龄大于等于28的用户
adults = session.query(User).filter(User.age >= 28).all()
print("年龄>=28的用户:")
for u in adults:
    print(f"  - {u.name} ({u.age}岁)")

# 排序查询：按年龄降序
sorted_users = session.query(User).order_by(User.age.desc()).all()
print("按年龄降序:")
for u in sorted_users:
    print(f"  - {u.name}: {u.age}岁")

# 聚合查询：统计平均年龄
from sqlalchemy import func
avg_age = session.query(func.avg(User.age)).scalar()
print(f"平均年龄: {avg_age:.1f}岁")
# 输出示例:
# 总用户数: 2
# 年龄>=28的用户:
#   - 李四 (30岁)
# 按年龄降序:
#   - 李四: 30岁
#   - 张三: 25岁
# 平均年龄: 27.5岁

session.close()
```

### 示例3：更新与删除（综合应用）

```python
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

engine = create_engine('sqlite:///demo.db')
Base = declarative_base()

class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    name = Column(String(50))
    age = Column(Integer)

Session = sessionmaker(bind=engine)
session = Session()

# 更新操作：将张三的年龄改为26
user_zhang = session.query(User).filter(User.name == '张三').first()
if user_zhang:
    user_zhang.age = 26  # 直接修改对象属性
    session.commit()
    print(f"已更新: {user_zhang.name} 的年龄改为 {user_zhang.age}")

# 删除操作：删除李四
user_li = session.query(User).filter(User.name == '李四').first()
if user_li:
    session.delete(user_li)  # 标记删除
    session.commit()
    print(f"已删除: {user_li.name}")

# 验证结果
remaining = session.query(User).all()
print(f"剩余用户数: {len(remaining)}")
for u in remaining:
    print(f"  - {u.name}: {u.age}岁")
# 输出示例:
# 已更新: 张三 的年龄改为 26
# 已删除: 李四
# 剩余用户数: 1
#   - 张三: 26岁

session.close()
```

---

## 4. 常见错误

### 错误1：忘记调用 `commit()`

```python
# 错误写法：数据不会真正写入数据库
user = User(name='王五', age=28)
session.add(user)
# 忘记 session.commit()
```

**原因**：`add()` 只是将对象加入会话，处于"待提交"状态。没有 `commit()`，事务不会持久化。

**正确写法**：
```python
user = User(name='王五', age=28)
session.add(user)
session.commit()  # 必须调用commit()才能保存
```

### 错误2：混淆 `filter()` 与 `filter_by()`

```python
# 错误写法：filter需要完整表达式
users = session.query(User).filter(name='张三').all()  # NameError: name 'name' is not defined

# 正确写法1：使用filter()，需要完整表达式
users = session.query(User).filter(User.name == '张三').all()

# 正确写法2：使用filter_by()，直接传关键字参数
users = session.query(User).filter_by(name='张三').all()
```

**原因**：`filter()` 接受的是Python表达式（需要 `Model.column` 形式），而 `filter_by()` 接受关键字参数（直接写列名）。

### 错误3：会话未关闭导致连接泄漏

```python
# 错误写法：每次操作都创建会话但不关闭
def get_user_count():
    session = Session()
    count = session.query(User).count()
    return count  # 没有session.close()

# 正确写法：使用上下文管理器或显式关闭
def get_user_count():
    session = Session()
    try:
        count = session.query(User).count()
        return count
    finally:
        session.close()  # 确保关闭

# 更推荐：使用上下文管理器
from contextlib import contextmanager

@contextmanager
def session_scope():
    session = Session()
    try:
        yield session
        session.commit()
    except:
        session.rollback()
        raise
    finally:
        session.close()

with session_scope() as session:
    count = session.query(User).count()
```

---

## 5. 练习

### 练习1：创建商品表并完成CRUD操作

**题目**：创建一个 `Product` 模型，包含字段：`id`（主键）、`name`（字符串）、`price`（浮点数）、`stock`（整数）。完成以下操作：
1. 插入3个商品数据
2. 查询价格大于50的商品
3. 将某个商品的价格上调10%
4. 删除库存为0的商品

**答案提示**：
```python
# 关键代码片段
class Product(Base):
    __tablename__ = 'products'
    id = Column(Integer, primary_key=True)
    name = Column(String(100))
    price = Column(Float)
    stock = Column(Integer)

# 查询价格>50
expensive = session.query(Product).filter(Product.price > 50).all()

# 更新价格
product.price *= 1.1  # 上调10%

# 删除库存为0
zero_stock = session.query(Product).filter(Product.stock == 0).all()
for p in zero_stock:
    session.delete(p)
session.commit()
```

### 练习2：实现多表关联查询

**题目**：创建 `Author`（作者）和 `Book`（书籍）两个模型，一个作者可以有多本书（一对多关系）。查询所有作者及其书籍数量。

**答案提示**：
```python
# 使用relationship建立关联
from sqlalchemy.orm import relationship
from sqlalchemy import ForeignKey

class Author(Base):
    __tablename__ = 'authors'
    id = Column(Integer, primary_key=True)
    name = Column(String(50))
    books = relationship('Book', back_populates='author')

class Book(Base):
    __tablename__ = 'books'
    id = Column(Integer, primary_key=True)
    title = Column(String(100))
    author_id = Column(Integer, ForeignKey('authors.id'))
    author = relationship('Author', back_populates='books')

# 查询作者及其书籍数量
from sqlalchemy import func
results = session.query(Author.name, func.count(Book.id)).join(Book).group_by(Author.id).all()
for name, count in results:
    print(f"作者: {name}, 书籍数量: {count}")
```

---

**本讲小结**：SQLAlchemy通过ORM思想将数据库操作转化为Python对象操作，大大提升了开发效率。掌握 `Engine`、`Session`、模型定义和CRUD操作是入门的关键。建议在真实项目中逐步实践，体会ORM带来的便利。